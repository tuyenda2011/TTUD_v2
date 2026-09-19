"""Test the files eligible for Git, without local caches or downloaded archives."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    repository = ROOT.parent
    listed = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", ROOT.name],
        cwd=repository,
    ).decode().split("\0")
    # A fresh directory makes this a working-tree packaging check, not a claim
    # that the uncommitted implementation is already available from git clone.
    destination = Path(tempfile.mkdtemp(prefix="warehouse-checkout-"))
    copied = 0
    for relative in sorted(set(listed) - {""}):
        source = repository / relative
        if not source.is_file():
            continue
        target = destination / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
                                "--basetemp", str(destination / ".pytest-work")],
                               cwd=destination, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    report = {"python": sys.executable, "directory": str(destination), "files": copied,
              "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    output = ROOT / "results/ui_audit/clean-checkout.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(completed.stdout)
    if completed.returncode:
        print(completed.stderr)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
