from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.config import APP_NAME, ADMIN_USERNAME, ADMIN_PASSWORD
from app.database import init_db, SessionLocal, AdminUser, now_ts
from app.utils.security import hash_password
from app.utils.response import fail
from app.routers.license import router as license_router
from app.routers.admin import router as admin_router
from app.routers.web_admin import router as web_admin_router

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app = FastAPI(title=APP_NAME)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return fail("请求过于频繁，请稍后再试", 429)


@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == ADMIN_USERNAME).first()
        if not admin:
            admin = AdminUser(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                is_active=1,
                created_at=now_ts(),
                updated_at=now_ts(),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(license_router)
app.include_router(admin_router)
app.include_router(web_admin_router)
