from pathlib import Path

WORKFLOW = Path(".github/workflows/ci.yml")


def test_ci_runs_required_day_four_gates() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "permissions:\n  contents: read",
        "  backend:",
        "  contracts-web:",
        "  public-boundary:",
        'python-version: "3.13.5"',
        'node-version: "24.18.0"',
        "python -m ruff check .",
        "python -m pytest",
        "python scripts/export_contracts.py --check",
        "npm --prefix apps/web run contracts:check",
        "npm --prefix apps/web test",
        "npm --prefix apps/web run typecheck",
        "npm --prefix apps/web run build",
        "./scripts/verify-public-boundary.ps1",
    ):
        assert required in text
    assert "needs:" not in text
