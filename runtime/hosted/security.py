from __future__ import annotations

import hashlib
import hmac
import time


class AuthenticationError(ValueError):
    pass


def body_digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical(timestamp: str, nonce: str, method: str, path: str, body: bytes) -> str:
    return "\n".join((timestamp, nonce, method.upper(), path, body_digest(body)))


def sign(secret: str, timestamp: str, nonce: str, method: str, path: str, body: bytes) -> str:
    return hmac.new(secret.encode(), canonical(timestamp, nonce, method, path, body).encode(), hashlib.sha256).hexdigest()


def verify(secret: str, headers: dict[str, str], method: str, path: str, body: bytes, *, now: int | None = None, max_skew: int = 300) -> str:
    lower = {key.lower(): value for key, value in headers.items()}
    timestamp = lower.get("x-repog-timestamp", "")
    nonce = lower.get("x-repog-nonce", "")
    supplied = lower.get("x-repog-signature", "")
    if not timestamp or not nonce or not supplied:
        raise AuthenticationError("Missing signed runtime headers.")
    try:
        issued_at = int(timestamp)
    except ValueError as exc:
        raise AuthenticationError("Invalid signed timestamp.") from exc
    if abs((now or int(time.time())) - issued_at) > max_skew:
        raise AuthenticationError("Expired signed request.")
    expected = sign(secret, timestamp, nonce, method, path, body)
    if not hmac.compare_digest(expected, supplied):
        raise AuthenticationError("Invalid runtime signature.")
    return nonce
