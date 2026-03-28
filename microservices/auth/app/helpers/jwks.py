import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings


def _b64url_uint(value: int) -> str:
    if value == 0:
        return "AA"
    length = (value.bit_length() + 7) // 8
    data = value.to_bytes(length, "big")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _calc_kid(n_b64: str, e_b64: str) -> str:
    digest = hashlib.sha256(f"{n_b64}.{e_b64}".encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def get_current_kid() -> str:
    public_key_pem = settings.AUTH_JWT_KEYS.public_key_path.read_text().encode("utf-8")
    public_key = serialization.load_pem_public_key(public_key_pem)

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Only RSA public keys are supported for JWKS")

    numbers = public_key.public_numbers()
    n_b64 = _b64url_uint(numbers.n)
    e_b64 = _b64url_uint(numbers.e)
    return _calc_kid(n_b64, e_b64)


def build_jwks() -> dict:
    public_key_pem = settings.AUTH_JWT_KEYS.public_key_path.read_text().encode("utf-8")
    public_key = serialization.load_pem_public_key(public_key_pem)

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Only RSA public keys are supported for JWKS")

    numbers = public_key.public_numbers()
    n_b64 = _b64url_uint(numbers.n)
    e_b64 = _b64url_uint(numbers.e)
    kid = _calc_kid(n_b64, e_b64)

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": settings.ALGORITHM,
        "kid": kid,
        "n": n_b64,
        "e": e_b64,
    }

    return {"keys": [jwk]}
