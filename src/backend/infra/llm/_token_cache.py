"""Shared Google Cloud token cache for Vertex AI clients.

Mirrors the token-caching strategy used in the benchmark harness:
obtain Application Default Credentials once, refresh only when the
token is about to expire (60-second margin), and reuse across all
Vertex AI client instances.
"""

import time
from typing import Optional

import google.auth
import google.auth.transport.requests


class _TokenCache:
    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expiry: float = 0.0

    def get(self) -> str:
        if not self._token or time.time() >= self._expiry - 60:
            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            creds.refresh(google.auth.transport.requests.Request())
            self._token = creds.token
            self._expiry = time.time() + 3500
        return self._token


token_cache = _TokenCache()


def auth_headers() -> dict[str, str]:
    """Return Authorization + Content-Type headers with a fresh bearer token."""
    return {
        "Authorization": f"Bearer {token_cache.get()}",
        "Content-Type": "application/json",
    }
