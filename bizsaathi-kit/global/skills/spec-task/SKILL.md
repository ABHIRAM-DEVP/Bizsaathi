---
name: spec-task
description: Turn a rough idea into a structured task file (docs/tasks/<slug>.md) with testable acceptance criteria before any code is written. Use for every feature or non-trivial fix. Does not implement.
argument-hint: "[rough idea]"
disable-model-invocation: true
---

# Write a task file for: $ARGUMENTS

Do not write code. Produce one file and stop.

1. Read AGENTS.md, docs/00-vision.md and any doc relevant to the idea. Look at one existing similar feature to copy its structure.
2. Ask at most 3 questions, and only if the answer would change the acceptance tests. Otherwise state assumptions in the file.
3. Size gate: if the work touches more than about 5 files, more than about 200 changed lines, or more than one concern, split it into docs/tasks/<slug>-01.md, -02.md, ... each independently shippable, with an explicit "depends on" line.
4. If `docs/tasks/_template.md` exists, copy its fields exactly and name the file `docs/tasks/<TASK_ID>-<kebab-slug>.md` (next free T-number). Otherwise write `docs/tasks/<kebab-slug>.md` (create the folder if needed) using this template:

```
# Task: <slug>
GOAL: <one sentence: an outcome a user can observe>
CONTEXT (read first): <file paths, docs, similar existing code>
CONSTRAINTS: <framework rules, versions, link .claude/rules/*.md>
INTERFACE: <signatures, request/response example, schema, UI states>
ACCEPTANCE:
  - Given <state> When <action> Then <result>      (each one maps to a test)
  - Command: just check-fast passes
OUT OF SCOPE: <explicit list>
PROCESS: tests first -> implement -> just check-fast -> report
REPORT: Changed / Ran / Not verified / Risks
```

5. Print the file path, a 5-line summary, and the assumptions you made. Then stop and wait for the human to review the file.
