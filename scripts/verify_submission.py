"""Verify an extracted submission without depending on the original machine path."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_research as study
from scripts.analyze_quality import verify_diagnostics
from src.models import InputError


def verify(root):
    root = root.resolve()
    metadata = json.loads((root / "SUBMISSION.json").read_text(encoding="utf-8"))
    for name, checksum in metadata["files_sha256"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise InputError(f"Missing or invalid submission path: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise InputError(f"Submission checksum mismatch: {name}")
    evidence = root / "evidence"
    count = study.verify(evidence / "study", study.checked_protocol(evidence / "study", mode="audit"))
    extra = verify_diagnostics(evidence / "study", evidence / "diagnostics")
    if count != metadata["study_solutions"] or extra != metadata["diagnostics_solutions"]:
        raise InputError("Submission evidence counts mismatch")
    print(f"Verified {len(metadata['files_sha256'])} files and {count + extra} solutions", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=ROOT)
    args = parser.parse_args()
    verify(args.directory)
