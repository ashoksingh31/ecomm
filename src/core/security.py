"""
JWT helpers.

ASSUMPTIONS.md #1 and #7 state that authentication already happened
upstream and every incoming request carries a valid JWT containing
`user_id` and `is_admin`. This module therefore only needs to be able to
DECODE (verify) tokens for the API layer, and ENCODE tokens so we have a
way to produce test tokens locally (see scripts/generate_test_token.py
and tests/conftest.py) without building a real login system, which is
explicitly out of scope.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config.settings import settings
from src.core.exceptions import InvalidTokenError


class TokenPayload:
    """Small typed wrapper around the claims we trust from the JWT."""

    def __init__(self, user_id: int, is_admin: bool):
        self.user_id = user_id
        self.is_admin = is_admin


def create_access_token(user_id: int, is_admin: bool = False, expires_minutes: int = 60 * 24) -> str:
    """
    Build a signed JWT. Only used by test fixtures / the dev token script -
    NOT exposed as a public API endpoint, since login/auth is out of scope.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"user_id": user_id, "is_admin": is_admin, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """
    Verify signature/expiry and pull out the two claims the rest of the
    app cares about. Raises InvalidTokenError on any failure so the API
    layer can turn it into a clean 401.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Could not validate credentials") from exc

    user_id = payload.get("user_id")
    is_admin = payload.get("is_admin", False)

    if user_id is None:
        raise InvalidTokenError("Token missing 'user_id' claim")

    return TokenPayload(user_id=user_id, is_admin=bool(is_admin))
