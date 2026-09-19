"""Safely extract and inventory unmodified author benchmark archives."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"
SOURCES = {
    "FoodmartData.zip": "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/batching/data/FoodmartData.zip",
    "HappyChicData.zip": "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/batching/data/HappyChicData.zip",
    "KrisSmallDataCorrected.zip": "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/data/KrisSmallDataCorrected.zip",
    "KrisLargeDataCorrected.zip": "https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/data/KrisLargeDataCorrected.zip",
}


def main():
    records = []
    for archive_name, url in SOURCES.items():
        path = ROOT / archive_name
        if not path.exists():
            raise SystemExit(f"Missing archive: {path}")
        destination = (ROOT / path.stem).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        files = []
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise SystemExit(f"CRC failure: {bad}")
            for member in archive.infolist():
                if member.is_dir() or "__MACOSX" in member.filename or Path(member.filename).name.startswith("._"):
                    continue
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination):
                    raise SystemExit(f"Unsafe archive path: {member.filename}")
                content = archive.read(member)
                if target.exists() and target.read_bytes() != content:
                    raise SystemExit(f"Refusing to overwrite changed raw data: {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(content)
                files.append({"file": target.relative_to(ROOT).as_posix(), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        with path.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append({"archive": archive_name, "url": url, "archive_bytes": path.stat().st_size, "sha256": sha, "files": files})
        print(f"{archive_name}: {len(files)} original files", flush=True)
    (ROOT / "manifest.json").write_text(json.dumps({"verified_at": datetime.now(timezone.utc).isoformat(), "note": "Archive bytes retained. Only macOS resource-fork entries excluded from extraction.", "datasets": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
