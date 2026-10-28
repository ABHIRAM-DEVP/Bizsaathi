---
name: write-prompt
description: Rewrite a vague request into a precise, testable prompt using the GOAL/CONTEXT/CONSTRAINTS/INTERFACE/ACCEPTANCE template. Use when the user pastes a rough idea and wants a prompt for a coding agent. Does not implement.
argument-hint: "[rough request]"
disable-model-invocation: true
---

# Rewrite as a prompt: $ARGUMENTS

Output the prompt only, in a code block, plus up to 3 open questions. Do not implement.

Rules:
- One outcome per prompt. If the request has several, output several prompts in dependency order.
- CONTEXT lists real file paths found with Grep/Glob, not guesses.
- ACCEPTANCE items are commands or given/when/then statements. Words like "good", "clean" and "robust" are not acceptance criteria.
- Include OUT OF SCOPE, because it prevents drive-by changes.
- Name the check command (`just check-fast`) and demand the Changed/Ran/Not verified/Risks report.

Template:

```
GOAL: <observable outcome>
CONTEXT: <paths to read first, similar existing code>
CONSTRAINTS: <stack versions, rules files, no new deps>
INTERFACE: <signatures, payloads, schema, UI states>
ACCEPTANCE:
  - Given/When/Then ...
  - just check-fast passes
OUT OF SCOPE: <list>
PROCESS: failing test first -> implement -> just check-fast -> report
REPORT: Changed / Ran / Not verified / Risks
```
