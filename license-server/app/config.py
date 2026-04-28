import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = os.getenv("APP_NAME", "License Server")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/license.db")
ALLOW_INSECURE_DEFAULTS = os.getenv("ALLOW_INSECURE_DEFAULTS", "").lower() in {"1", "true", "yes"}

# 生产版使用 RS256：服务端持有 private.pem，客户端只持有 public.pem。
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", str(BASE_DIR / "keys" / "private.pem"))
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", str(BASE_DIR / "keys" / "public.pem"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")
INSECURE_ADMIN_PASSWORDS = {"admin123456", "change-me", "changeme", "password"}
