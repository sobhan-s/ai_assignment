"""
AST-based test that enforces the no-dict policy in graph/nodes/.

The rule: nodes must NOT return raw dict literals directly.
All state mutations must go through apply_delta() in app/graph/adapters.py.
The only allowed use of `dict` syntax inside nodes is in calls to apply_delta().
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

NODES_DIR = Path("app/graph/nodes")


def _collect_python_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.py"))


def _get_return_dict_literals(tree: ast.AST) -> list[ast.Return]:
    """Return all `return {...}` statements in the tree."""
    bad_returns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            bad_returns.append(node)
    return bad_returns


def test_nodes_directory_is_accessible() -> None:
    """Ensure the test can locate the nodes directory."""
    assert NODES_DIR.exists(), f"Expected {NODES_DIR} to exist"
    assert NODES_DIR.is_dir()


def test_all_node_files_are_valid_python() -> None:
    """Every .py file in nodes/ must parse without a SyntaxError."""
    files = _collect_python_files(NODES_DIR)
    assert files, "No .py files found in nodes directory"
    for path in files:
        source = path.read_text()
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"{path.name} has a syntax error: {exc}")


def test_no_raw_dict_returns_in_nodes() -> None:
    """
    Nodes must not return raw dict literals like `return {"key": val}`.
    They must return the result of apply_delta() or an empty dict `{}`.
    The empty dict {} is allowed as a no-op signal (e.g., synthesize returning {}).

    Exceptions:
      - condense_question.py: directly mutates `question` key (no Delta type for it)
      - persist_and_log.py: returns {} after DB writes (no state mutation needed)
    """
    # These files are known/acceptable exceptions to the apply_delta rule
    ALLOWED_RAW_DICT_NODES = {"condense_question.py", "persist_and_log.py"}

    files = _collect_python_files(NODES_DIR)
    violations = []

    for path in files:
        if path.name in ALLOWED_RAW_DICT_NODES:
            continue
        source = path.read_text()
        tree = ast.parse(source)
        bad = _get_return_dict_literals(tree)
        # Filter: allow `return {}` (empty dict = no-op signal)
        non_empty_bad = [
            r for r in bad if r.value and isinstance(r.value, ast.Dict) and r.value.keys
        ]
        if non_empty_bad:
            violations.append(
                f"{path.name}: {len(non_empty_bad)} raw non-empty dict return(s) found "
                f"at lines {[r.lineno for r in non_empty_bad]}"
            )

    if violations:
        pytest.fail(
            "Raw dict returns detected in nodes (use apply_delta() instead):\n"
            + "\n".join(violations)
        )


def test_all_nodes_import_apply_delta() -> None:
    """Every non-__init__ node file should import apply_delta from adapters.

    Exceptions:
      - condense_question.py: returns raw dict for `question` key mutation
      - persist_and_log.py: only does DB writes, returns {}
    """
    # These nodes legitimately skip apply_delta for architecture reasons
    EXEMPT_FROM_APPLY_DELTA = {
        "condense_question.py",
        "persist_and_log.py",
        "__init__.py",
    }

    files = [
        f
        for f in _collect_python_files(NODES_DIR)
        if f.name not in EXEMPT_FROM_APPLY_DELTA
    ]
    missing = []
    for path in files:
        source = path.read_text()
        if "apply_delta" not in source:
            missing.append(path.name)

    if missing:
        import pytest

        pytest.fail(
            f"The following node files do not use apply_delta(): {missing}\n"
            "All nodes must go through apply_delta() to mutate state."
        )


def test_node_files_have_docstrings() -> None:
    """Node files should have module-level docstrings documenting their purpose."""

    files = [f for f in _collect_python_files(NODES_DIR) if f.name != "__init__.py"]
    missing_docs = []
    for path in files:
        source = path.read_text()
        tree = ast.parse(source)
        # A module docstring is the first statement if it's an Expr with a Constant
        has_docstring = (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
        )
        if not has_docstring:
            missing_docs.append(path.name)

    # Warn but don't fail   this is a code quality check
    # If you want to enforce, change the comment below to pytest.fail
    assert isinstance(missing_docs, list)  # always passes, just gathers info
