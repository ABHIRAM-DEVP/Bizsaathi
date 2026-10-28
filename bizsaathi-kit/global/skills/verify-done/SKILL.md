---
name: verify-done
description: Use before reporting any task as complete, or when asked whether something works. Runs the project's check command and maps every acceptance criterion to real evidence.
---

# Verify before claiming done

## Current diff scope
!`git diff --stat 2>/dev/null || true`

## Steps
1. Find the check command: `just check` if a justfile exists, otherwise the "Commands" section of AGENTS.md. Run it. Capture the exit code and the last lines of output.
2. If it fails, the task is NOT done. Report the failure plainly. Do not soften it.
3. Read the task file's ACCEPTANCE list (docs/tasks/<slug>.md). For each criterion, point to evidence: a test name that passed, or a command and its output. A criterion without evidence is "NOT VERIFIED".
4. Compare the diff above with the task scope. List any file changed outside the scope.
5. Reply with the 7-part report from the global CLAUDE.md (Completed, Files changed, Verification, Not completed, Assumptions, Risks, Next task). Under Verification list each acceptance criterion on its own line with evidence or NOT VERIFIED.

Never write "should work" or "looks good". Either you ran it or you did not.
