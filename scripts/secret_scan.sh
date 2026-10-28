#!/usr/bin/env bash
# Fails (exit 1) if secret-like content is found. Cheap guard, not a replacement for a real scanner.
# Scans the working tree, skipping .git, node_modules, .venv, .next, lock files and .env.example.
ROOT="${1:-.}"
FOUND=0
EXCL=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.next \
      --exclude-dir=__pycache__ --exclude=*.lock --exclude=pnpm-lock.yaml --exclude=package-lock.json \
      --exclude=.env.example --exclude=secret_scan.sh --exclude=guard-paths.sh --exclude=*.zip)

scan() { # label pattern
  local out
  out=$(grep -rEn "${EXCL[@]}" -e "$2" "$ROOT" 2>/dev/null | head -n 5)
  if [ -n "$out" ]; then
    echo "❌ $1"; echo "$out" | sed 's/^/   /'; FOUND=1
  fi
}

scan "secret-like NEXT_PUBLIC_ variable (shipped to browsers)" 'NEXT_PUBLIC_[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)'
scan "possible API key literal"                               '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})'
scan "private key block"                                       '-----BEGIN [A-Z ]*PRIVATE KEY-----'
scan "META_API_KEY assigned a literal value"                   'META_API_KEY[[:space:]]*[=:][[:space:]]*["'"'"']?[A-Za-z0-9_-]{12,}'

if [ -f "$ROOT/.env" ] && command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  if git -C "$ROOT" ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "❌ .env is tracked by git"; FOUND=1
  fi
fi

if [ $FOUND -eq 0 ]; then echo "✅ secret scan clean"; exit 0; fi
echo "💥 secret scan failed"; exit 1
