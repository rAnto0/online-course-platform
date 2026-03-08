from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .config import settings

TOKEN_TYPE_FIELD = "type"


def get_password_hash(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password)


def create_jwt(
    token_type: str,
    token_data: dict[str, Any],
    private_key: str = "",
    algorithm: str = settings.ALGORITHM,
    expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    expires_delta: timedelta | None = None,
) -> str:
    if not private_key:
        private_key = settings.AUTH_JWT_KEYS.private_key_path.read_text()

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=expires_minutes))

    jwt_payload = {
        TOKEN_TYPE_FIELD: token_type,
        "exp": expire,
        "iat": now,
    }
    jwt_payload.update(token_data)

    return jwt.encode(jwt_payload, private_key, algorithm=algorithm)


def decode_jwt(
    token: str | bytes,
    public_key: str = "",
    algorithm: str = settings.ALGORITHM,
) -> dict[str, Any]:
    if not public_key:
        public_key = settings.AUTH_JWT_KEYS.public_key_path.read_text()

    decoded = jwt.decode(token, public_key, algorithms=[algorithm])

    return decoded
