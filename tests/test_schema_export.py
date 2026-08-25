import json

from cultureshift.schema_export import (
    SCHEMA_RELATIVE_PATH,
    check_contract_schema,
    render_contract_schema,
    write_contract_schema,
)


def test_contract_schema_is_deterministic_and_contains_public_definitions() -> None:
    first = render_contract_schema()
    second = render_contract_schema()
    assert first == second
    assert first.endswith("\n")
    schema = json.loads(first)
    assert schema["title"] == "ContractRegistry"
    assert "RunCreate" in schema["$defs"]
    assert {
        "CritiqueCompleted",
        "CritiqueIssue",
        "RevisionChange",
        "RevisionCompleted",
    }.issubset(schema["$defs"])
    statuses = set(schema["$defs"]["CritiqueStatus"]["enum"])
    assert statuses == {"pass", "revise", "needs_human_review", "reject"}
    assert set(schema["$defs"]["RevisionChange"]["enum"]) == {
        "shorten_headline",
        "shorten_body",
    }


def test_write_and_check_detect_stale_contract_schema(tmp_path) -> None:
    path = write_contract_schema(tmp_path)
    assert path == tmp_path / SCHEMA_RELATIVE_PATH
    assert check_contract_schema(tmp_path)

    path.write_text("{}\n", encoding="utf-8", newline="\n")
    assert not check_contract_schema(tmp_path)
