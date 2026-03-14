import logging
from typing import Any

import jwt

from app.core.config import settings

logger = logging.getLogger("app.core.security")

_public_key_cache: str | None = None


def load_public_key() -> None:
    global _public_key_cache
    _public_key_cache = settings.AUTH_JWT_PUBLIC_KEY.read_text()
    logger.debug("JWT public key loaded from %s", settings.AUTH_JWT_PUBLIC_KEY)


def decode_jwt(
    token: str | bytes,
    public_key: str | None = None,
    algorithm: str = settings.ALGORITHM,
) -> dict[str, Any]:
    if public_key is None:
        global _public_key_cache
        if _public_key_cache is None:
            _public_key_cache = settings.AUTH_JWT_PUBLIC_KEY.read_text()
        public_key = _public_key_cache

    decoded = jwt.decode(token, public_key, algorithms=[algorithm])

    return decoded
