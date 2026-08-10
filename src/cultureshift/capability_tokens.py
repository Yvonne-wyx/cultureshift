from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


class Capability(StrEnum):
    READ_PROJECT_RUN = "project_run:read"
    UPDATE_PROJECT_RUN = "project_run:update"


@dataclass(frozen=True)
class CapabilityClaims:
    subject: str
    audience: str
    capabilities: frozenset[Capability]
    issued_at: datetime
    expires_at: datetime


class CapabilityTokenError(ValueError):
    """A deliberately non-specific capability-token verification failure."""


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


class CapabilityTokenService:
    """Issues short-lived, HMAC-authenticated, least-privilege capability tokens."""

    def __init__(self, *, secret: bytes, audience: str) -> None:
        if len(secret) < 32:
            raise ValueError("capability token secret must be at least 32 bytes")
        if not audience:
            raise ValueError("audience is required")
        self._secret = secret
        self._audience = audience

    def issue(
        self,
        *,
        subject: str,
        capabilities: set[Capability],
        ttl: timedelta,
        now: datetime | None = None,
    ) -> str:
        if not subject or not capabilities:
            raise ValueError("subject and at least one capability are required")
        if ttl <= timedelta(0):
            raise ValueError("ttl must be positive")
        issued_at = now or datetime.now(UTC)
        if issued_at.tzinfo is None or issued_at.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        payload = {
            "aud": self._audience,
            "cap": sorted(capability.value for capability in capabilities),
            "exp": int((issued_at + ttl).timestamp()),
            "iat": int(issued_at.timestamp()),
            "sub": subject,
            "v": 1,
        }
        encoded = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signature = _encode(hmac.digest(self._secret, encoded.encode("ascii"), hashlib.sha256))
        return f"{encoded}.{signature}"

    def verify(
        self,
        token: str,
        *,
        required: Capability,
        now: datetime | None = None,
    ) -> CapabilityClaims:
        try:
            encoded, supplied_signature = token.split(".", maxsplit=1)
            expected_signature = _encode(
                hmac.digest(self._secret, encoded.encode("ascii"), hashlib.sha256)
            )
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise CapabilityTokenError("invalid capability token")
            payload: dict[str, Any] = json.loads(_decode(encoded))
            capabilities = frozenset(Capability(value) for value in payload["cap"])
            verified_at = now or datetime.now(UTC)
            if verified_at.tzinfo is None or verified_at.utcoffset() is None:
                raise CapabilityTokenError("invalid capability token")
            if payload.get("v") != 1 or payload["aud"] != self._audience:
                raise CapabilityTokenError("invalid capability token")
            if required not in capabilities or int(verified_at.timestamp()) >= payload["exp"]:
                raise CapabilityTokenError("invalid capability token")
            return CapabilityClaims(
                subject=payload["sub"],
                audience=payload["aud"],
                capabilities=capabilities,
                issued_at=datetime.fromtimestamp(payload["iat"], UTC),
                expires_at=datetime.fromtimestamp(payload["exp"], UTC),
            )
        except CapabilityTokenError:
            raise
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise CapabilityTokenError("invalid capability token") from error
