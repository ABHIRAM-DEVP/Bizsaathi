#!/usr/bin/env python3
"""Cross-platform task runner for BizSaathi (provides parity with justfile when just is not installed)."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(cmd: str, cwd: Path = ROOT) -> int:
    print(f">> {cmd} (in {cwd})")
    ret = subprocess.run(cmd, shell=True, cwd=cwd)
    return ret.returncode

def recipe_guards() -> int:
    # 1. secret scan
    r1 = run("bash scripts/secret_scan.sh")
    if r1 != 0:
        return r1
    # 2. eval validate
    r2 = run(f"{sys.executable} -X utf8 scripts/eval_validate.py")
    if r2 != 0:
        return r2
    # 3. check docs
    r3 = run(f"{sys.executable} -X utf8 scripts/check_docs.py")
    return r3

def recipe_check_fast() -> int:
    rg = recipe_guards()
    if rg != 0:
        return rg
    backend = ROOT / "backend"
    r_api = run("uv run pytest tests/unit -x -q", cwd=backend)
    if r_api != 0:
        return r_api
    frontend = ROOT / "frontend"
    r_web = run("npm run lint", cwd=frontend)
    return r_web

def recipe_check() -> int:
    rcf = recipe_check_fast()
    if rcf != 0:
        return rcf
    backend = ROOT / "backend"
    r_ruff = run("uv run ruff check .", cwd=backend)
    if r_ruff != 0:
        return r_ruff
    r_mypy = run("uv run mypy .", cwd=backend)
    if r_mypy != 0:
        return r_mypy
    frontend = ROOT / "frontend"
    r_build = run("npm run build", cwd=frontend)
    return r_build

def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "guards"
    if target == "guards":
        return recipe_guards()
    elif target == "check-fast":
        return recipe_check_fast()
    elif target == "check":
        return recipe_check()
    else:
        print(f"Unknown recipe '{target}'. Available: guards, check-fast, check")
        return 1

if __name__ == "__main__":
    sys.exit(main())

