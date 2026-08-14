from __future__ import annotations

import os

from cultureshift.asset_storage import TemporaryAssetStore


def main() -> int:
    configured = os.environ.get("CULTURESHIFT_TEMP_ASSET_DIR", "")
    if not configured.strip():
        raise SystemExit("CULTURESHIFT_TEMP_ASSET_DIR is required")
    removed = TemporaryAssetStore(configured).purge_expired()
    print(f"purged: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
