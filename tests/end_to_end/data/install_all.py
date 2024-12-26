#!/usr/bin/env python3

from pathlib import Path
import subprocess

def main() -> int:
    here = Path(__file__).parent.resolve()

    for dep_dir in (here / "deps").iterdir():
        _run_pip_install(dep_dir)

    for pkg_dir in here.glob("test_pkg_*"):
        _run_pip_install(pkg_dir)

    return 0

def _run_pip_install(directory: Path) -> None:
   subprocess.check_call(("pip", "install", "."), cwd=directory)


if __name__ == '__main__':
    raise SystemExit(main())
