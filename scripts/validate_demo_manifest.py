"""Validate the fail-closed demo asset manifest contract."""

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

SUPPORTED_RIGHTS_STATUSES = {"cleared", "restricted", "prohibited"}
EXPLICIT_PERMISSIONS = {"permitted", "prohibited"}
FIXTURE_ASSET_PREFIX = "apps/web/public/fixtures/"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def is_safe_fixture_asset_path(value):
    if not isinstance(value, str) or not value.startswith(FIXTURE_ASSET_PREFIX):
        return False
    if "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return path.is_absolute() is False and ".." not in path.parts


def validate_manifest(manifest):
    errors = []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]
    if manifest.get("manifest_version") != 1:
        errors.append("manifest_version must be 1")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return errors + ["assets must be a JSON array"]

    seen_ids = set()
    for index, asset in enumerate(assets):
        label = f"asset[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{label}: asset must be a JSON object")
            continue

        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            errors.append(f"{label}: missing asset id")
        elif asset_id in seen_ids:
            errors.append(f"{label}: duplicate asset id: {asset_id}")
        else:
            seen_ids.add(asset_id)

        if "asset_path" not in asset:
            errors.append(f"{label}: missing asset path")
        elif not is_safe_fixture_asset_path(asset["asset_path"]):
            errors.append(f"{label}: asset path must be safe")

        if not isinstance(asset.get("sha256"), str) or not SHA256_PATTERN.fullmatch(
            asset["sha256"]
        ):
            errors.append(f"{label}: sha256 must be lowercase 64-character hexadecimal")

        provenance = asset.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            errors.append(f"{label}: missing provenance")

        if "rights_status" not in asset:
            errors.append(f"{label}: missing rights status")
        elif asset["rights_status"] not in SUPPORTED_RIGHTS_STATUSES:
            errors.append(f"{label}: unsupported rights status")

        if asset.get("derivative_work_permission") not in EXPLICIT_PERMISSIONS:
            errors.append(f"{label}: derivative-work permission must be explicit")
        if asset.get("public_display_permission") not in EXPLICIT_PERMISSIONS:
            errors.append(f"{label}: public-display permission must be explicit")

    return errors


def validate_asset_integrity(manifest, repository_root):
    """Verify structurally safe manifest entries against repository file bytes."""
    errors = []
    root = repository_root.resolve()
    for index, asset in enumerate(manifest["assets"]):
        label = f"asset[{index}]"
        relative_path = PurePosixPath(asset["asset_path"])
        asset_path = (root / Path(*relative_path.parts)).resolve()
        try:
            asset_path.relative_to(root)
        except ValueError:
            errors.append(f"{label}: asset file is outside repository")
            continue
        if not asset_path.is_file():
            errors.append(f"{label}: asset file is missing or not a regular file")
            continue
        digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if digest != asset["sha256"]:
            errors.append(f"{label}: asset sha256 does not match file bytes")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: validate_demo_manifest.py MANIFEST", file=sys.stderr)
        return 2
    try:
        manifest = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"manifest could not be read as JSON: {error}", file=sys.stderr)
        return 1

    errors = validate_manifest(manifest)
    if not errors:
        errors.extend(validate_asset_integrity(manifest, REPOSITORY_ROOT))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("demo asset manifest is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
