#!/usr/bin/env python3
"""Consistency checks between the planning docs (stdlib only). Exit 0 if consistent, 1 otherwise.

Checks
 1. Every API path in docs/08-api-spec.md also appears in docs/14-endpoint-specs.md.
 2. Every EP-xxx id cited in docs/prompts/BUILD-PHASES.md exists in docs/14-endpoint-specs.md.
 3. docs/schema/reference_schema.sql: parentheses balance per statement, every REFERENCES target is a table in the
    file, and every table has business_id unless it is in the allowlist.
 4. Every docs/NN-name.md path mentioned in AGENTS.md, CLAUDE.md and README files exists.
This is a structure check only. It does NOT prove the SQL runs; apply it to real Postgres in task T-103.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
errors = []


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# 1. endpoint paths
t08, t14 = read(DOCS / "08-api-spec.md"), read(DOCS / "14-endpoint-specs.md")
prefixes = ("auth", "me", "business", "uploads", "products", "jobs", "posts", "approvals", "public", "widget.js",
            "conversations", "customers", "orders", "payments", "audit-log", "guardrail", "reports", "disputes",
            "dashboard", "channels", "push", "notifications", "webhooks", "evaluations", "metrics", "evidence")
pat = re.compile(r"(?<![\w/.])(/(?:%s)(?:[A-Za-z0-9_{}./-]*[A-Za-z0-9_}])?)" % "|".join(re.escape(p) for p in prefixes))
paths08 = sorted(set(pat.findall(t08)))
for p in paths08:
    if p not in t14:
        errors.append(f"path in docs/08 missing from docs/14: {p}")

# 2. EP ids
ids14 = set(re.findall(r"EP-[A-Z]\d{2}", t14))
phases = DOCS / "prompts" / "BUILD-PHASES.md"
for i in sorted(set(re.findall(r"EP-[A-Z]\d{2}", read(phases)))):
    if i not in ids14:
        errors.append(f"BUILD-PHASES cites unknown endpoint id {i}")

# 3. reference schema structure
sql = read(DOCS / "schema" / "reference_schema.sql")
sql_nocomment = re.sub(r"--[^\n]*", "", sql)
tables = re.findall(r"CREATE TABLE (\w+)\s*\(", sql_nocomment)
allow_no_tenant = {"business", "otp_challenge"}
for m in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", sql_nocomment, re.S):
    name, body = m.group(1), m.group(2)
    if body.count("(") != body.count(")"):
        errors.append(f"unbalanced parentheses in table {name}")
    if name not in allow_no_tenant and "business_id" not in body:
        errors.append(f"table {name} has no business_id")
for ref in re.findall(r"REFERENCES (\w+)\s*\(", sql_nocomment):
    if ref not in tables:
        errors.append(f"REFERENCES unknown table {ref}")
if sql_nocomment.count("(") != sql_nocomment.count(")"):
    errors.append("unbalanced parentheses in reference_schema.sql")

# 4. doc path mentions
texts = [read(ROOT / "AGENTS.md"), read(ROOT / "CLAUDE.md")]
for rp in list(DOCS.rglob("README.md")):
    texts.append(read(rp))
for p in sorted(set(m for t in texts for m in re.findall(r"docs/[0-9A-Za-z_./-]+\.(?:md|sql)", t))):
    if "<" in p:
        continue
    if not (ROOT / p).exists():
        errors.append(f"referenced file missing: {p}")

if errors:
    print("❌ docs consistency check failed")
    for e in errors[:40]:
        print("   " + e)
    sys.exit(1)
print(f"✅ docs consistent: {len(paths08)} api paths in docs/08 all present in docs/14, {len(ids14)} endpoint ids, "
      f"{len(tables)} tables structurally checked")
