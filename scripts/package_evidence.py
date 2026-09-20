"""Validate every benchmark run, then archive evidence with a SHA-256 sidecar."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.models import read_instance
from src.solver import fingerprint
from src.validator import validate_solution


def package(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError("Archive must be outside the evidence directory")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    instances = {fingerprint(instance): instance for instance in
                 (read_instance(p) for p in (source / "instances").glob("*.json"))}
    runs = manifest["runs"]
    if not runs:
        raise ValueError("No runs to package")
    for run in runs:
        path = (source / run["file"]).resolve()
        if not path.is_relative_to(source):
            raise ValueError("Run path escapes evidence directory")
        result = json.loads(path.read_text(encoding="utf-8"))
        instance = instances[run["instance_sha256"]]
        if result.get("instance_sha256") != fingerprint(instance):
            raise ValueError(f"Fingerprint mismatch: {path.name}")
        errors = validate_solution(instance, result)
        if errors:
            raise ValueError(f"{path.name}: {errors}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{checksum}  {output.name}\n", encoding="utf-8")
    print(f"Validated {len(runs)} runs; archive: {output}; SHA-256: {checksum}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.source, args.output)
