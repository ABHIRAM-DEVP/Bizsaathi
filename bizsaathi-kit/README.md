# BizSaathi Agentic Setup Kit

Spec-first, evidence-based setup for building BizSaathi with Claude Code (or any agent that reads AGENTS.md). It turns your master brief and BizSaathi 2.0 plan into files an agent loads, hooks that enforce rules, docs to review, an eval dataset and the prompts to run in order.

## The idea in four lines
1. Facts live in files (AGENTS.md, docs/, task files), not in chat.
2. "Done" is a command (`just check`), enforced by a Stop hook, not a sentence from a model.
3. Models propose; deterministic code and independent controls verify; the seller approves.
4. Nothing is claimed that was not run: mocks are labelled, Meta API facts are UNVERIFIED until checked.

## Install
```
# once per machine (merge if you already have ~/.claude/CLAUDE.md)
cp global/CLAUDE.md ~/.claude/CLAUDE.md
cp -r global/skills global/agents ~/.claude/

# per repo (includes dotfiles)
cp -r project/. /path/to/bizsaathi/
cd /path/to/bizsaathi && chmod +x .claude/hooks/*.sh scripts/*.sh scripts/*.py
git init   # if new; then: just guards
```
Needs: `jq` (hooks), `just`, python3. Later: uv, pnpm, Docker. On Windows run the scripts from Git Bash or WSL, and keep `.sh` files on LF line endings.

## What is inside
| Path | Purpose |
|---|---|
| global/ | Honesty rules, 4 skills (`/verify-done`, `/debug-fast`, `/spec-task`, `/write-prompt`), 3 subagents (reviewer, test-runner, debugger) |
| project/AGENTS.md, CLAUDE.md | Project contract (stack, commands, definition of done, non-negotiables). CLAUDE.md imports AGENTS.md |
| project/apps/api/CLAUDE.md, apps/api/app/agents/CLAUDE.md, apps/web/CLAUDE.md | Folder-specific rules, loaded when Claude works there |
| project/.claude/rules/ | Scoped rules: agents (verifiable agents), meta-models, db-tenancy, security, web-pwa, api, testing, evals |
| project/.claude/skills/ | `/new-agent-node`, `/new-endpoint`, `/add-migration`, `/new-page`, `/add-eval-case` |
| project/.claude/agents/ | implementer, security-reviewer, eval-analyst |
| project/.claude/settings.json + hooks/ | Permissions (live Meta calls need approval) and hooks: path/secret guard, Stop gate running `just check-fast` |
| project/justfile, docker-compose.yml, .env.example | One command set; local Postgres+pgvector, Redis, MinIO; env template with no values |
| project/scripts/ | `secret_scan.sh`, `eval_validate.py`, `api_smoke.sh` (emoji reporter) |
| project/evals/ | Dataset schema, 16 labelled synthetic cases, thresholds (TODO until baseline), README |
| project/docs/00-13 | Vision, architecture (15-node graph, sequences), data model, UI/PWA, tests, troubleshooting, requirements (REQ ids), agent catalog, API spec (MVP/STRETCH/FUTURE), verifiable agents, multimodal agent, Muse open models/Fireworks, assumptions/risks/deps, demo script |
| project/docs/PHASES.md, tasks/, adr/ | Phases and milestones; seeded Phase 1 tasks T-101 to T-106; ADR template + ADR-0001 |
| project/docs/14-endpoint-specs.md | Per-endpoint spec for every route (EP ids): auth, request, response, errors, rules, key tests |
| project/docs/15-schema-and-formats.md, docs/schema/reference_schema.sql | Data types, enums, formats, envelopes, proposal payloads, redaction, naming; reference DDL for 29 tables (design reference, not yet run on a database) |
| project/docs/prompts/BUILD-PHASES.md | Detailed build prompts for Phases 1 to 5 (about 25 prompts plus gates), each with goal, endpoints, data, Given/When/Then acceptance |
| project/docs/prompts/ | Your prompts 1-8 intact, plus 9 (verify Meta API), 10 (implement a task), 11 (A/B/C eval), and the run order |
| project/docs/source/ | Your master brief and the BizSaathi 2.0 attachment |

## Your three named topics: what they became (and what is unverified)
| Topic | Where | Honest status |
|---|---|---|
| Build a multimodal AI agent | docs/10-multimodal-agent.md, agent catalog nodes 02, 04, 05, 11, skills, rules | Pattern and contracts written from your plan. Meta API details UNVERIFIED. The session itself was not retrievable |
| Agents 102: verifiable agents | docs/09-verifiable-agents.md, .claude/rules/agents.md, nodes 10/11/13, evals | Principles written from your brief and a third-party best-practices page. The session itself was not retrievable. Reconcile with the talk's notes |
| Specialized intelligence on Fireworks with Muse open models | docs/11-muse-open-models.md | Facts from Fireworks pages and a third-party listing, labelled by source. Fireworks training page does not mention Muse; fine-tuning Muse there is UNVERIFIED. Kept as a FUTURE/optional experiment |

## First hour
1. Install (above). `just guards` should print two green lines.
2. Answer the open items in docs/12 (deadline, credits, team size, tool versions).
3. Run Prompt 1, then Prompt 9 (needs your Meta key; it will ask before the live call), then 2, 3, 4, 5. Then Prompt 10 per task.
4. Daily: `/spec-task` -> review -> implementer -> reviewer -> `just check`.

## What was tested here, and what was not
Tested with fixtures: guard-paths hook (blocks generated client, lockfiles, .env, edits to existing migrations, NEXT_PUBLIC secrets, key-looking text; allows new migrations and .env.example), secret_scan.sh (clean on the kit; fails on bad fixtures), eval_validate.py (valid dataset passes; bad one fails), api_smoke.sh (pass and fail paths), settings.json parses, and the Stop gate (block and allow cases, via a stand-in `just`).
Not tested: the justfile recipes beyond `guards` (no app code exists, `just` not installed in the build environment), docker-compose.yml, any Meta API call, the PWA, and whether your Claude Code version loads every hook (run `/hooks` once).
Not verified: all Meta model IDs, endpoints, prices and credit amounts; the hackathon deadline; Fireworks/Muse facts beyond their source pages.

## Known limits
- This kit makes false "done" claims visible and expensive; it does not make a weak model equal a strong one on hard design.
- The Stop hook runs only `check-fast`. Run `just check` before reporting done.
- Eval thresholds are TODO on purpose. Set them after a baseline run; never to make a run pass.
- `just eval-mock`, `just meta-smoke` and the eval runner are commands your code must provide (tasks T-104 and Phase 5); the kit defines the contract, not the implementation.
