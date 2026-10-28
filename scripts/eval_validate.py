#!/usr/bin/env python3
"""Validate evals/dataset/cases.jsonl against the rules in evals/dataset/schema.json (stdlib only).

Exit 0 when valid, 1 otherwise. Usage: python3 scripts/eval_validate.py [path/to/cases.jsonl]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evals" / "dataset" / "cases.jsonl"
SCHEMA = ROOT / "evals" / "dataset" / "schema.json"

def main() -> int:
    if not CASES.exists() or not SCHEMA.exists():
        print(f"❌ missing {CASES if not CASES.exists() else SCHEMA}")
        return 1
    schema = json.loads(SCHEMA.read_text())
    cats = set(schema["categories"])
    splits = set(schema["splits"])
    sources = set(schema["sources"])
    decisions = set(schema["decisions"])
    required = schema["required_fields"]
    errors, seen, n = [], set(), 0
    per_cat = {c: 0 for c in cats}
    for ln, line in enumerate(CASES.read_text().splitlines(), 1):
        if not line.strip():
            continue
        n += 1
        try:
            c = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {ln}: invalid JSON ({e})"); continue
        for f in required:
            if f not in c:
                errors.append(f"line {ln}: missing field '{f}'")
        cid = c.get("id")
        if cid in seen:
            errors.append(f"line {ln}: duplicate id {cid}")
        seen.add(cid)
        if c.get("category") not in cats:
            errors.append(f"line {ln}: bad category {c.get('category')!r}")
        else:
            per_cat[c["category"]] += 1
        if c.get("split") not in splits:
            errors.append(f"line {ln}: bad split {c.get('split')!r}")
        if c.get("source") not in sources:
            errors.append(f"line {ln}: bad source {c.get('source')!r}")
        exp = c.get("expected", {})
        if not isinstance(exp, dict) or exp.get("decision") not in decisions:
            errors.append(f"line {ln}: expected.decision must be one of {sorted(decisions)}")
        if not isinstance(c.get("input"), dict):
            errors.append(f"line {ln}: input must be an object")
    if n == 0:
        errors.append("no cases found")
    if errors:
        print("❌ eval dataset invalid")
        for e in errors[:25]:
            print("   " + e)
        return 1
    missing = [c for c, k in per_cat.items() if k == 0]
    print(f"✅ eval dataset valid: {n} cases, {len(seen)} unique ids")
    if missing:
        print(f"⚠️  categories with zero cases: {', '.join(sorted(missing))}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
