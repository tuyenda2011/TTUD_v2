"""Build a portable source/test/evidence submission with per-file checksums."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_research as study
from scripts.analyze_quality import verify_diagnostics
from src.models import InputError


def package(quality, output, extra_evidence=()):
    quality, output = quality.resolve(), output.resolve()
    if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
        raise InputError("Refusing to overwrite a submission")
    if output.is_relative_to(quality):
        raise InputError("Submission must be outside its evidence directory")
    count = study.verify(quality / "study", study.checked_protocol(quality / "study", mode="audit"))
    extra = verify_diagnostics(quality / "study", quality / "diagnostics")
    entries = {}
    supplements = [Path(path).resolve() for path in extra_evidence]
    if len({path.name for path in supplements}) != len(supplements):
        raise InputError("Supplemental evidence directory names must be unique")
    for path in supplements:
        if not path.is_dir() or output.is_relative_to(path):
            raise InputError("Supplemental evidence must be a directory outside the submission output")
    for folder in ("src", "demo", "scripts", "tests", "configs", "data/processed", "data/synthetic", "docs"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".json", ".md", ".html", ".css", ".js"):
                if not path.resolve().is_relative_to(ROOT):
                    raise InputError("Submission source escapes workspace")
                entries[path.relative_to(ROOT).as_posix()] = path
    for name in ("README.md", "pyproject.toml", "requirements.txt", "DESIGN.md", "ALGORITHM_NOTES.md", "QUALITY_RESULTS.md", ".streamlit/config.toml", "data/README.md",
                 "data/raw/manifest.json", "data/raw/KrisSmallDataCorrected/small/instances_100_1.txt"):
        path = ROOT / name
        if not path.is_file():
            raise InputError(f"Missing submission file: {name}")
        entries[name] = path
    for directory, prefix in [(quality, "evidence/"), *[(p, f"evidence/supplemental/{p.name}/") for p in supplements]]:
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".prof", ".zip") and not path.name.endswith(".zip.sha256"):
                if not path.resolve().is_relative_to(directory):
                    raise InputError("Evidence file escapes its directory")
                entries[prefix + path.relative_to(directory).as_posix()] = path
    files = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sorted(entries.items())}
    metadata = {"format_version": 1, "study_solutions": count, "diagnostics_solutions": extra,
                "files_sha256": files,
                "supplemental_evidence": [f"evidence/supplemental/{path.name}" for path in supplements],
                "verify": "python scripts/verify_submission.py .",
                "run": "python -m streamlit run demo/app.py",
                "note": "Academic report and full raw archives are separate. Processed inputs, tests, technical docs, source provenance and one original author-data test fixture are included. Historical reports describe the run-time verifier; the later sealed audit records current verification code."}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as bundle:
        for name, path in sorted(entries.items()):
            bundle.write(path, name)
        bundle.writestr("SUBMISSION.json", json.dumps(metadata, indent=2) + "\n")
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{checksum}  {output.name}\n", encoding="utf-8")
    print(f"Packaged {len(entries)} files, {count + extra} solutions: {output}", flush=True)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extra-evidence", type=Path, action="append", default=[],
                        help="Include supplemental verification artifacts (repeatable)")
    args = parser.parse_args()
    package(args.quality, args.output, args.extra_evidence)
