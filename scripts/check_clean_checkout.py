"""Test the files eligible for Git, without local caches or downloaded archives."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    repository = ROOT
    listed = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository,
    ).decode().split("\0")
    required = [repository / "src", repository / "pyproject.toml"]
    missing = [str(path.relative_to(repository)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Clean-checkout prerequisites missing: {', '.join(missing)}")
    # A fresh directory makes this a working-tree packaging check, not a claim
    # that the uncommitted implementation is already available from git clone.
    destination = Path(tempfile.mkdtemp(prefix="warehouse-checkout-"))
    copied = 0
    for relative in sorted(set(listed) - {""}):
        source = repository / relative
        if not source.is_file():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    test_files = [path for path in listed if path.startswith("tests/")]
    if test_files:
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
                                    "--basetemp", str(destination / ".pytest-work")],
                                   cwd=destination, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    else:
        exit_code = 0
        stdout = "Public checkout intentionally omits local tests; source layout check passed.\n"
        stderr = ""
    report = {"python": sys.executable, "directory": str(destination), "files": copied,
              "tests_included": bool(test_files), "exit_code": exit_code,
              "stdout": stdout, "stderr": stderr}
    output = ROOT / "results/ui_audit/clean-checkout.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(stdout)
    if exit_code:
        print(stderr)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
