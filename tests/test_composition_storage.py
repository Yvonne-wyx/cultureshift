from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from cultureshift.composition_storage import (
    CompositionArtifactError,
    CompositionArtifactStore,
)

PNG = b"\x89PNG\r\n\x1a\nday12-fixture-output"


def test_composition_store_is_integrity_checked_and_immutable(tmp_path) -> None:
    store = CompositionArtifactStore(tmp_path / "compositions")
    artifact_id = uuid4()
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    first = store.save(artifact_id, PNG, expires_at=now + timedelta(hours=24))
    replay = store.save(artifact_id, PNG, expires_at=now + timedelta(hours=24))
    loaded = store.load(artifact_id, now=now)

    assert replay == first
    assert loaded.record == first
    assert loaded.png_bytes == PNG
    assert not list((tmp_path / "compositions").glob("*.part"))
    with pytest.raises(CompositionArtifactError):
        store.save(artifact_id, PNG + b"drift", expires_at=now + timedelta(hours=24))


def test_composition_store_rejects_expired_missing_and_oversized_artifacts(tmp_path) -> None:
    store = CompositionArtifactStore(tmp_path / "compositions", max_bytes=32)
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    artifact_id = uuid4()
    store.save(artifact_id, PNG, expires_at=now + timedelta(seconds=1))

    with pytest.raises(CompositionArtifactError):
        store.load(artifact_id, now=now + timedelta(seconds=1))
    with pytest.raises(CompositionArtifactError):
        store.load(uuid4(), now=now)
    with pytest.raises(CompositionArtifactError):
        store.save(uuid4(), b"x" * 33, expires_at=now + timedelta(hours=1))


def test_composition_store_deletes_a_materialized_artifact(tmp_path) -> None:
    store = CompositionArtifactStore(tmp_path / "compositions")
    artifact_id = uuid4()
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    store.save(artifact_id, PNG, expires_at=now + timedelta(hours=1))
    assert store.delete(artifact_id) is True
    assert store.delete(artifact_id) is False
