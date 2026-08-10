import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate_demo_manifest.py"


def valid_asset():
    return {
        "id": "synthetic-ai-app-static-ad-001",
        "asset_type": "static_advertising_creative",
        "provenance": {
            "source_class": "synthetic_example",
            "description": "Project-created metadata-only example.",
        },
        "creator_owner_status": "project_created",
        "rights_status": "cleared",
        "permitted_project_use": ["repository_test", "public_demo"],
        "derivative_work_permission": "permitted",
        "public_display_permission": "permitted",
        "attribution_required": False,
        "attribution_text": None,
        "evidence_reference": "demo/assets/RIGHTS.md",
        "notes": "Synthetic contract fixture; no binary asset is included.",
    }


class DemoManifestValidatorTests(unittest.TestCase):
    def run_validator(self, manifest):
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(manifest_path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def assert_rejected(self, manifest, expected_message):
        result = self.run_validator(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(expected_message, result.stderr)

    def test_accepts_valid_synthetic_demo_manifest(self):
        result = self.run_validator({"manifest_version": 1, "assets": [valid_asset()]})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_missing_asset_id(self):
        asset = valid_asset()
        del asset["id"]
        self.assert_rejected({"manifest_version": 1, "assets": [asset]}, "missing asset id")

    def test_rejects_duplicate_asset_id(self):
        asset = valid_asset()
        self.assert_rejected(
            {"manifest_version": 1, "assets": [asset, asset.copy()]},
            "duplicate asset id",
        )

    def test_rejects_missing_provenance(self):
        asset = valid_asset()
        del asset["provenance"]
        self.assert_rejected({"manifest_version": 1, "assets": [asset]}, "missing provenance")

    def test_rejects_missing_rights_status(self):
        asset = valid_asset()
        del asset["rights_status"]
        self.assert_rejected({"manifest_version": 1, "assets": [asset]}, "missing rights status")

    def test_rejects_unsupported_rights_status(self):
        asset = valid_asset()
        asset["rights_status"] = "probably_allowed"
        self.assert_rejected(
            {"manifest_version": 1, "assets": [asset]}, "unsupported rights status"
        )

    def test_rejects_unknown_derivative_work_permission(self):
        asset = valid_asset()
        asset["derivative_work_permission"] = "unknown"
        self.assert_rejected(
            {"manifest_version": 1, "assets": [asset]},
            "derivative-work permission must be explicit",
        )

    def test_rejects_unknown_public_display_permission(self):
        asset = valid_asset()
        asset["public_display_permission"] = "unknown"
        self.assert_rejected(
            {"manifest_version": 1, "assets": [asset]},
            "public-display permission must be explicit",
        )

    def test_rejects_invalid_top_level_structure(self):
        self.assert_rejected([], "manifest must be a JSON object")


if __name__ == "__main__":
    unittest.main()
