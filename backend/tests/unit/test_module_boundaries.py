"""Module boundary tests ensuring strict separation between Agents and Execution Service."""

import ast
from pathlib import Path


def test_agents_cannot_import_execution_service():
    """Verify that no code in app/agents imports the execution service."""
    agents_dir = Path(__file__).resolve().parent.parent.parent / "app" / "agents"
    assert agents_dir.exists(), "app/agents directory must exist"

    python_files = list(agents_dir.rglob("*.py"))
    assert len(python_files) > 0, "app/agents must contain python source files"

    forbidden_tokens = ["ExecutionService", "app.services.execution"]

    for py_file in python_files:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for token in forbidden_tokens:
                        assert token not in alias.name, (
                            f"VIOLATION: {py_file} imports '{alias.name}'. "
                            f"Agents must NEVER import the execution service."
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for token in forbidden_tokens:
                    assert token not in module, (
                        f"VIOLATION: {py_file} imports from '{module}'. Agents must NEVER import the execution service."
                    )
                for alias in node.names:
                    assert alias.name != "ExecutionService", (
                        f"VIOLATION: {py_file} imports ExecutionService. "
                        f"Agents must NEVER import the execution service."
                    )
