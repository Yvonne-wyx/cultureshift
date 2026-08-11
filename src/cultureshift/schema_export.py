from __future__ import annotations

import json
from pathlib import Path

from cultureshift.contracts import ContractRegistry

SCHEMA_RELATIVE_PATH = Path("contracts/json-schema/cultureshift.contracts.schema.json")


def render_contract_schema() -> str:
    schema = ContractRegistry.model_json_schema(by_alias=True)
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_contract_schema(repo_root: Path) -> Path:
    path = repo_root / SCHEMA_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_contract_schema().encode("utf-8"))
    return path


def check_contract_schema(repo_root: Path) -> bool:
    path = repo_root / SCHEMA_RELATIVE_PATH
    return path.is_file() and path.read_bytes() == render_contract_schema().encode("utf-8")
