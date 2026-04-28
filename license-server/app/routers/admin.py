from __future__ import annotations

import time
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jose import JWTError
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD
from app.database import get_db, License, LicenseDevice, ActivationLog, AdminUser, now_ts
from app.services.token_service import create_admin_token, decode_license_token
from app.utils.response import ok, fail
from app.utils.security import generate_license_key, hash_password, verify_password

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateLicenseRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=500)
    productCode: str = "default"
    plan: str = "standard"
    maxDevices: int = Field(default=1, ge=1, le=100)
    expireDays: Optional[int] = Field(default=365, ge=1)
    note: Optional[str] = None


class ExtendRequest(BaseModel):
    days: int = Field(..., ge=1)


def require_admin(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = authorization.replace("Bearer ", "", 1)
    try:
        payload = decode_license_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")
    if payload.get("type") != "admin":
        raise HTTPException(status_code=401, detail="invalid token")
    admin = db.query(AdminUser).filter(AdminUser.id == int(payload.get("sub"))).first()
    if not admin or admin.is_active != 1:
        raise HTTPException(status_code=403, detail="admin disabled")
    return admin


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not admin or not verify_password(req.password, admin.password_hash):
        return fail("用户名或密码错误", 401)
    token = create_admin_token(admin.id, admin.username)
    return ok({"token": token})


@router.post("/licenses")
def create_licenses(req: CreateLicenseRequest, db: Session = Depends(get_db), admin=Depends(require_admin)):
    expire_at = None
    if req.expireDays:
        expire_at = int(time.time()) + req.expireDays * 86400

    result = []
    for _ in range(req.count):
        key = generate_license_key()
        item = License(
            license_key=key,
            product_code=req.productCode,
            plan=req.plan,
            max_devices=req.maxDevices,
            expire_at=expire_at,
            is_active=1,
            note=req.note,
            created_at=now_ts(),
            updated_at=now_ts(),
        )
        db.add(item)
        result.append(key)
    db.commit()
    return ok({"keys": result})


@router.get("/licenses")
def list_licenses(db: Session = Depends(get_db), admin=Depends(require_admin)):
    rows = db.query(License).order_by(License.id.desc()).limit(500).all()
    data = []
    for x in rows:
        active_devices = db.query(LicenseDevice).filter(LicenseDevice.license_id == x.id, LicenseDevice.is_revoked == 0).count()
        data.append({
            "id": x.id,
            "licenseKey": x.license_key,
            "productCode": x.product_code,
            "plan": x.plan,
            "maxDevices": x.max_devices,
            "activeDevices": active_devices,
            "expireAt": x.expire_at,
            "isActive": bool(x.is_active),
            "note": x.note,
            "createdAt": x.created_at,
        })
    return ok({"items": data})


@router.post("/licenses/{license_id}/disable")
def disable_license(license_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    item = db.query(License).filter(License.id == license_id).first()
    if not item:
        return fail("授权不存在", 404)
    item.is_active = 0
    item.updated_at = now_ts()
    db.commit()
    return ok(msg="disabled")


@router.post("/licenses/{license_id}/enable")
def enable_license(license_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    item = db.query(License).filter(License.id == license_id).first()
    if not item:
        return fail("授权不存在", 404)
    item.is_active = 1
    item.updated_at = now_ts()
    db.commit()
    return ok(msg="enabled")


@router.post("/licenses/{license_id}/extend")
def extend_license(license_id: int, req: ExtendRequest, db: Session = Depends(get_db), admin=Depends(require_admin)):
    item = db.query(License).filter(License.id == license_id).first()
    if not item:
        return fail("授权不存在", 404)
    base = item.expire_at if item.expire_at and item.expire_at > int(time.time()) else int(time.time())
    item.expire_at = base + req.days * 86400
    item.updated_at = now_ts()
    db.commit()
    return ok({"expireAt": item.expire_at})


@router.get("/licenses/{license_id}/devices")
def list_devices(license_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    rows = db.query(LicenseDevice).filter(LicenseDevice.license_id == license_id).order_by(LicenseDevice.id.desc()).all()
    return ok({"items": [{
        "id": x.id,
        "machineFingerprint": x.machine_fingerprint,
        "hostname": x.hostname,
        "platform": x.platform,
        "arch": x.arch,
        "appVersion": x.app_version,
        "firstActivatedAt": x.first_activated_at,
        "lastSeenAt": x.last_seen_at,
        "isRevoked": bool(x.is_revoked),
    } for x in rows]})


@router.post("/devices/{device_id}/revoke")
def revoke_device(device_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    item = db.query(LicenseDevice).filter(LicenseDevice.id == device_id).first()
    if not item:
        return fail("设备不存在", 404)
    item.is_revoked = 1
    db.commit()
    return ok(msg="revoked")


@router.get("/logs")
def list_logs(db: Session = Depends(get_db), admin=Depends(require_admin)):
    rows = db.query(ActivationLog).order_by(ActivationLog.id.desc()).limit(500).all()
    return ok({"items": [{
        "id": x.id,
        "licenseId": x.license_id,
        "licenseKey": x.license_key,
        "machineFingerprint": x.machine_fingerprint,
        "ip": x.ip,
        "action": x.action,
        "success": bool(x.success),
        "message": x.message,
        "createdAt": x.created_at,
    } for x in rows]})
