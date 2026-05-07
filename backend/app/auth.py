from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from .config import settings


def require_token(x_tester_token: str | None = Header(default=None)) -> None:
    """Reject requests that don't carry the shared secret."""
    expected = settings.api_token
    if not expected:
        # Fail closed: if the server wasn't configured with a token, no requests work.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is missing FLUTTER_TESTER_TOKEN; refusing all requests.",
        )
    if not x_tester_token or not hmac.compare_digest(x_tester_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Tester-Token.",
        )
