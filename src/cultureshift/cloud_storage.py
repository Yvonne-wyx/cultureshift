from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ObjectStorageError(RuntimeError):
    pass


class ObjectNotFoundError(ObjectStorageError):
    pass


class ObjectStore(Protocol):
    def put(self, key: str, content: bytes, *, content_type: str, create_only: bool) -> None: ...

    def get(self, key: str, *, max_bytes: int) -> bytes: ...

    def delete(self, keys: tuple[str, ...]) -> int: ...

    def list(self, prefix: str) -> tuple[str, ...]: ...


class SupabaseObjectStore:
    """Private Supabase Storage bucket accessed only with a server-side service key."""

    def __init__(self, base_url: str, service_key: str, bucket: str = "cultureshift-private"):
        if not base_url.startswith("https://") or not service_key.strip() or not bucket.strip():
            raise ValueError("valid private object storage configuration is required")
        self._base_url = base_url.rstrip("/")
        self._service_key = service_key
        self._bucket = bucket

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
        not_found: bool = False,
        max_bytes: int = 256 * 1024,
    ) -> bytes:
        request = Request(
            f"{self._base_url}/storage/v1{path}",
            data=body,
            method=method,
            headers={
                "apikey": self._service_key,
                "Authorization": f"Bearer {self._service_key}",
                **dict(headers or {}),
            },
        )
        try:
            with urlopen(request, timeout=15) as response:  # noqa: S310
                content = response.read(max_bytes + 1)
        except HTTPError as error:
            if not_found:
                try:
                    detail = json.loads(error.read(64 * 1024))
                except (OSError, TypeError, ValueError, json.JSONDecodeError):
                    detail = {}
                reported_status = str(detail.get("statusCode", ""))
                reported_error = str(detail.get("error", "")).casefold()
                if error.code == 404 or reported_status == "404" or reported_error == "not_found":
                    raise ObjectNotFoundError("object unavailable") from None
            raise ObjectStorageError("object storage request failed") from None
        except (OSError, URLError, TimeoutError):
            raise ObjectStorageError("object storage request failed") from None
        if len(content) > max_bytes:
            raise ObjectStorageError("object storage response exceeded limit")
        return content

    def put(self, key: str, content: bytes, *, content_type: str, create_only: bool) -> None:
        self._request(
            "POST",
            f"/object/{quote(self._bucket, safe='')}/{quote(key, safe='/')}",
            body=content,
            headers={"Content-Type": content_type, "x-upsert": str(not create_only).lower()},
            max_bytes=64 * 1024,
        )

    def get(self, key: str, *, max_bytes: int) -> bytes:
        return self._request(
            "GET",
            f"/object/{quote(self._bucket, safe='')}/{quote(key, safe='/')}",
            not_found=True,
            max_bytes=max_bytes,
        )

    def delete(self, keys: tuple[str, ...]) -> int:
        if not keys:
            return 0
        self._request(
            "DELETE",
            f"/object/{quote(self._bucket, safe='')}",
            body=json.dumps({"prefixes": list(keys)}, separators=(",", ":")).encode(),
            headers={"Content-Type": "application/json"},
        )
        return len(keys)

    def list(self, prefix: str) -> tuple[str, ...]:
        payload = self._request(
            "POST",
            f"/object/list/{quote(self._bucket, safe='')}",
            body=json.dumps({"prefix": prefix, "limit": 1000}, separators=(",", ":")).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            rows = json.loads(payload)
            return tuple(
                f"{prefix}{row['name']}" for row in rows if isinstance(row.get("name"), str)
            )
        except (TypeError, ValueError, KeyError):
            raise ObjectStorageError("object storage response invalid") from None
