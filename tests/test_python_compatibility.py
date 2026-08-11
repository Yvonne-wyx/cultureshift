import ast
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_type_alias_type_uses_python_311_backport_with_direct_dependency() -> None:
    contracts_tree = ast.parse(
        (REPO_ROOT / "src/cultureshift/contracts.py").read_text(encoding="utf-8")
    )
    backport_names = {
        alias.name
        for node in contracts_tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "typing_extensions"
        for alias in node.names
    }
    assert "TypeAliasType" in backport_names

    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "typing-extensions>=4.12,<5" in project["project"]["dependencies"]
