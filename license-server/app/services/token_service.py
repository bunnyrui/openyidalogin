import time
from functools import lru_cache
from jose import jwt
from app.config import JWT_ALGORITHM, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH


@lru_cache(maxsize=1)
def get_private_key() -> str:
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def get_public_key() -> str:
    with open(PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def create_license_token(license_obj, machine_fingerprint: str) -> str:
    payload = {
        "sub": str(license_obj.id),
        "type": "license",
        "productCode": license_obj.product_code,
        "plan": license_obj.plan,
        "machineFingerprint": machine_fingerprint,
        "expireAt": license_obj.expire_at,
        "issuedAt": int(time.time()),
    }
    return jwt.encode(payload, get_private_key(), algorithm=JWT_ALGORITHM)


def decode_license_token(token: str) -> dict:
    return jwt.decode(token, get_public_key(), algorithms=[JWT_ALGORITHM])


def create_admin_token(admin_id: int, username: str) -> str:
    now = int(time.time())
    payload = {
        "sub": str(admin_id),
        "username": username,
        "type": "admin",
        "iat": now,
        "exp": now + 86400,
    }
    return jwt.encode(payload, get_private_key(), algorithm=JWT_ALGORITHM)
