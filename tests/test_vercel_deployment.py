import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_routes_one_public_surface_to_frontend_and_fastapi() -> None:
    configuration = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))

    assert configuration["services"]["frontend"]["root"] == "apps/web"
    assert configuration["services"]["api"]["root"] == "."
    assert configuration["services"]["api"]["entrypoint"] == "cultureshift.app:app"
    assert configuration["rewrites"] == [
        {"source": "/api/(.*)", "destination": {"service": "api"}},
        {"source": "/(.*)", "destination": {"service": "frontend"}},
    ]


def test_public_environment_template_documents_cloud_persistence() -> None:
    template = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "CULTURESHIFT_DATABASE_URL=" in template
    assert "CULTURESHIFT_OBJECT_STORAGE_URL=" in template
    assert "CULTURESHIFT_OBJECT_STORAGE_KEY=" in template
