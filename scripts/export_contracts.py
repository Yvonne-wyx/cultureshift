from __future__ import annotations

import argparse
from pathlib import Path

from cultureshift.schema_export import (
    SCHEMA_RELATIVE_PATH,
    check_contract_schema,
    write_contract_schema,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CultureShift public contracts")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    relative = SCHEMA_RELATIVE_PATH.as_posix()
    if args.check:
        if check_contract_schema(REPO_ROOT):
            print(f"current: {relative}")
            return 0
        print(f"stale: {relative}")
        return 1
    write_contract_schema(REPO_ROOT)
    print(f"wrote: {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
