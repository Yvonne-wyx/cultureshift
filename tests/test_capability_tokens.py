from datetime import UTC, datetime, timedelta

import pytest

from cultureshift.capability_tokens import (
    Capability,
    CapabilityTokenError,
    CapabilityTokenService,
)


def test_issue_and_verify_scoped_capability_token() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")

    token = service.issue(
        subject="run-123",
        capabilities={Capability.READ_PROJECT_RUN},
        ttl=timedelta(minutes=5),
        now=now,
    )
    claims = service.verify(
        token,
        required=Capability.READ_PROJECT_RUN,
        now=now + timedelta(minutes=1),
    )

    assert claims.subject == "run-123"
    assert claims.capabilities == frozenset({Capability.READ_PROJECT_RUN})


@pytest.mark.parametrize(
    "mutation", ["tamper", "wrong-audience", "wrong-secret", "wrong-scope", "expired"]
)
def test_capability_token_fails_closed(mutation: str) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    token = service.issue(
        subject="run-123",
        capabilities={Capability.READ_PROJECT_RUN},
        ttl=timedelta(seconds=30),
        now=now,
    )

    verifier = service
    required = Capability.READ_PROJECT_RUN
    verify_at = now
    if mutation == "tamper":
        token = token[:-1] + ("A" if token[-1] != "A" else "B")
    elif mutation == "wrong-audience":
        verifier = CapabilityTokenService(secret=b"a" * 32, audience="other-api")
    elif mutation == "wrong-secret":
        verifier = CapabilityTokenService(secret=b"b" * 32, audience="cultureshift-api")
    elif mutation == "wrong-scope":
        required = Capability.UPDATE_PROJECT_RUN
    else:
        verify_at = now + timedelta(seconds=31)

    with pytest.raises(CapabilityTokenError):
        verifier.verify(token, required=required, now=verify_at)


def test_capability_token_rejects_noncanonical_signature_encoding() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    token = service.issue(
        subject="run-123",
        capabilities={Capability.READ_PROJECT_RUN},
        ttl=timedelta(minutes=1),
        now=now,
    )
    payload, signature = token.split(".")
    replacement = "B" if signature[-1] == "A" else "A"

    with pytest.raises(CapabilityTokenError):
        service.verify(
            f"{payload}.{signature[:-1]}{replacement}",
            required=Capability.READ_PROJECT_RUN,
            now=now,
        )


def test_token_service_rejects_short_secret_and_non_positive_ttl() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        CapabilityTokenService(secret=b"short", audience="api")

    service = CapabilityTokenService(secret=b"a" * 32, audience="api")
    with pytest.raises(ValueError, match="positive"):
        service.issue(
            subject="run-123",
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(0),
        )
