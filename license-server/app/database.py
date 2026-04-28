import time
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def now_ts():
    return int(time.time())


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(128), unique=True, nullable=False, index=True)
    product_code = Column(String(64), nullable=False, default="default", index=True)
    plan = Column(String(32), nullable=False, default="standard")
    max_devices = Column(Integer, nullable=False, default=1)
    expire_at = Column(Integer, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    note = Column(Text, nullable=True)
    created_at = Column(Integer, nullable=False, default=now_ts)
    updated_at = Column(Integer, nullable=False, default=now_ts)

    devices = relationship("LicenseDevice", back_populates="license")


class LicenseDevice(Base):
    __tablename__ = "license_devices"
    __table_args__ = (
        UniqueConstraint("license_id", "machine_fingerprint", name="uix_license_machine"),
    )

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    machine_id = Column(String(255), nullable=True)
    machine_fingerprint = Column(String(128), nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    platform = Column(String(64), nullable=True)
    arch = Column(String(64), nullable=True)
    app_version = Column(String(64), nullable=True)
    first_activated_at = Column(Integer, nullable=False, default=now_ts)
    last_seen_at = Column(Integer, nullable=False, default=now_ts)
    is_revoked = Column(Integer, nullable=False, default=0)

    license = relationship("License", back_populates="devices")


class ActivationLog(Base):
    __tablename__ = "activation_logs"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, nullable=True, index=True)
    license_key = Column(String(128), nullable=True, index=True)
    machine_fingerprint = Column(String(128), nullable=True, index=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    action = Column(String(64), nullable=False, index=True)
    success = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    created_at = Column(Integer, nullable=False, default=now_ts)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(Integer, nullable=False, default=now_ts)
    updated_at = Column(Integer, nullable=False, default=now_ts)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
