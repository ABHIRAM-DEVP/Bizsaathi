import os
import sys
import re
import json
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

PATTERNS = {
    "AI / Cloud API Key": re.compile(r'(?:AIza[0-9A-Za-z-_]{35}|sk-[a-zA-Z0-9_-]{20,}|sk-ant-[a-zA-Z0-9_-]{20,}|nvapi-[a-zA-Z0-9_-]{20,}|AKIA[0-9A-Z]{16})'),
    "OAuth / Token Literal": re.compile(r'(?:ghp|gho|ghu|ghs|ghr|github_pat)_[a-zA-Z0-9_]{16,}|xox[baprs]-[0-9a-zA-Z]{10,}'),
    "Private Key": re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    "Database URL with Credentials": re.compile(r'(?:postgres|postgresql|mysql|mongodb|redis)://(?!(?:app:app|bizsaathi:bizsaathi|localhost|redis:6379))[^:\s\'"]+:[^@\s\'"]+@'),
    "Hardcoded Password Assignment": re.compile(r'(?i)(?:password|passwd|pwd|secret_key)\s*[:=]\s*["\']([^"\']{4,})["\']'),
}

EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', 'venv', '.next', '__pycache__', '.pytest_cache', '.ruff_cache', 'dist', 'build'}
EXCLUDE_FILES = {'pnpm-lock.yaml', 'package-lock.json', 'uv.lock', 'final_safe_check.py'}

MOCK_OR_TEST_VALUES = {
    'change-me', 'minioadmin', 'password', 'password123', 'secret_password_123',
    'unit-test-secret', 'unit-test-secret-never-use-as-model-id', 'unit-test-secret-never-log',
    'unit-test-pooled-secret', 'unit-test-timeout-secret', 'unit-test-stream-secret',
    'seller1', 'a-strong-local-password', 'secure-local-password', 'wrong-password',
    'Synthetic-test-password-2026', 'incorrect-synthetic-password',
    'Another-synthetic-password-2026', 'Other-synthetic-password-2026',
    'previous-account-pass', 'integration-account-pass', 'db-test',
    'runtime-test', 'owner-test', 'new-password', 'current-password', 'supersecret',
    'some-key', 'bearer-opaque-token'
}

def scan_repository():
    results = {
        "files_scanned": 0,
        "code_files_scanned": 0,
        "high_risk_findings": [],
        "benign_test_findings": [],
        "gitignored_env_files": [],
        "tracked_env_files": []
    }

    # 1. Check tracked files for .env
    for target_repo in ['.', 'frontend']:
        p = os.path.join(ROOT_DIR, target_repo)
        if os.path.exists(os.path.join(p, '.git')):
            try:
                tracked = subprocess.check_output(['git', '-C', p, 'ls-files'], text=True, errors='ignore').splitlines()
                for f in tracked:
                    if ('.env' in f or 'id_rsa' in f) and not f.endswith('.example'):
                        results["tracked_env_files"].append(f"{target_repo}/{f}")
            except Exception:
                pass

    # 2. Scan every file
    code_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.sql', '.sh', '.yml', '.yaml', '.toml', '.ini', '.md', '.html'}

    for root, dirs, files in os.walk(ROOT_DIR, topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in EXCLUDE_FILES:
                continue
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, ROOT_DIR)
            results["files_scanned"] += 1

            # Check if env file
            if os.path.basename(f).startswith('.env') and not f.endswith('.example'):
                results["gitignored_env_files"].append(rel_path)
                continue

            ext = os.path.splitext(f)[1].lower()
            if ext in code_extensions or f in {'Dockerfile', 'justfile'}:
                results["code_files_scanned"] += 1

            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    for line_no, line in enumerate(fp, 1):
                        stripped = line.strip()
                        for category, pat in PATTERNS.items():
                            match = pat.search(stripped)
                            if match:
                                # Determine if test / benign
                                matched_text = match.group(0)
                                is_test = False
                                for tv in MOCK_OR_TEST_VALUES:
                                    if tv in stripped:
                                        is_test = True
                                        break
                                
                                item = {
                                    "file": rel_path,
                                    "line": line_no,
                                    "category": category,
                                    "snippet": stripped[:120]
                                }
                                if is_test or 'tests/' in rel_path.replace('\\', '/') or 'test_' in rel_path:
                                    results["benign_test_findings"].append(item)
                                else:
                                    results["high_risk_findings"].append(item)
            except Exception:
                continue

    return results

if __name__ == '__main__':
    data = scan_repository()
    print(json.dumps(data, indent=2))

