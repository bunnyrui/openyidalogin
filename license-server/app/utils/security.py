import secrets
import string
from passlib.context import CryptContext

# 使用 pbkdf2_sha256，避免 bcrypt 72 字节密码长度限制。
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password or "")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password or "", password_hash)
    except Exception:
        return False


def generate_license_key(prefix="LIC") -> str:
    alphabet = string.ascii_uppercase + string.digits
    parts = []
    for _ in range(4):
        parts.append("".join(secrets.choice(alphabet) for _ in range(4)))
    return f"{prefix}-" + "-".join(parts)
