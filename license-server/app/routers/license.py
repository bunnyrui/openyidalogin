from __future__ import annotations

import time
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db, License, LicenseDevice, now_ts
from app.services.token_service import create_license_token, decode_license_token
from app.services.log_service import write_log
from app.utils.response import ok, fail

router = APIRouter(prefix="/api/v1/license", tags=["license"])


class ActivateRequest(BaseModel):
    licenseKey: str = Field(..., min_length=4)
    machineId: Optional[str] = None
    machineFingerprint: str = Field(..., min_length=16)
    hostname: Optional[str] = None
    platform: Optional[str] = None
    arch: Optional[str] = None
    appVersion: Optional[str] = None


class VerifyRequest(BaseModel):
    licenseToken: str
    machineFingerprint: str
    appVersion: Optional[str] = None


def _client_ip(request: Request):
    return request.headers.get("x-forwarded-for", request.client.host if request.client else "")


@router.post("/activate")
def activate(req: ActivateRequest, request: Request, db: Session = Depends(get_db)):
    key = req.licenseKey.strip().upper()
    license_obj = db.query(License).filter(License.license_key == key).first()

    if not license_obj:
        write_log(db, license_key=key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="activate_failed", success=False, message="license not found")
        return fail("卡密不存在", 404)

    if license_obj.is_active != 1:
        write_log(db, license_id=license_obj.id, license_key=key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="activate_failed", success=False, message="license disabled")
        return fail("卡密已被禁用", 403)

    now = int(time.time())
    if license_obj.expire_at and license_obj.expire_at < now:
        write_log(db, license_id=license_obj.id, license_key=key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="activate_failed", success=False, message="license expired")
        return fail("卡密已过期", 403)

    existed = db.query(LicenseDevice).filter(
        LicenseDevice.license_id == license_obj.id,
        LicenseDevice.machine_fingerprint == req.machineFingerprint,
    ).first()

    if existed:
        if existed.is_revoked == 1:
            return fail("该设备已被解绑或封禁，请联系管理员", 403)
        existed.last_seen_at = now_ts()
        existed.app_version = req.appVersion
        db.commit()
    else:
        active_count = db.query(LicenseDevice).filter(
            LicenseDevice.license_id == license_obj.id,
            LicenseDevice.is_revoked == 0,
        ).count()
        if active_count >= license_obj.max_devices:
            write_log(db, license_id=license_obj.id, license_key=key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="activate_failed", success=False, message="device limit exceeded")
            return fail("设备数量已达上限", 403)

        device = LicenseDevice(
            license_id=license_obj.id,
            machine_id=req.machineId,
            machine_fingerprint=req.machineFingerprint,
            hostname=req.hostname,
            platform=req.platform,
            arch=req.arch,
            app_version=req.appVersion,
            first_activated_at=now_ts(),
            last_seen_at=now_ts(),
            is_revoked=0,
        )
        db.add(device)
        db.commit()

    token = create_license_token(license_obj, req.machineFingerprint)
    write_log(db, license_id=license_obj.id, license_key=key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="activate_success", success=True, message="activated")

    return ok({
        "licenseToken": token,
        "expireAt": license_obj.expire_at,
        "plan": license_obj.plan,
        "maxDevices": license_obj.max_devices,
    }, "activated")


@router.post("/verify")
def verify(req: VerifyRequest, request: Request, db: Session = Depends(get_db)):
    try:
        payload = decode_license_token(req.licenseToken)
    except JWTError:
        return fail("授权文件无效", 401)

    if payload.get("machineFingerprint") != req.machineFingerprint:
        return fail("设备不匹配", 403)

    license_id = int(payload.get("sub"))
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj or license_obj.is_active != 1:
        return fail("授权已被禁用", 403)

    now = int(time.time())
    if license_obj.expire_at and license_obj.expire_at < now:
        return fail("授权已过期", 403)

    device = db.query(LicenseDevice).filter(
        LicenseDevice.license_id == license_obj.id,
        LicenseDevice.machine_fingerprint == req.machineFingerprint,
    ).first()
    if not device or device.is_revoked == 1:
        return fail("设备未绑定或已解绑", 403)

    device.last_seen_at = now_ts()
    device.app_version = req.appVersion
    db.commit()

    write_log(db, license_id=license_obj.id, license_key=license_obj.license_key, machine_fingerprint=req.machineFingerprint, ip=_client_ip(request), user_agent=request.headers.get("user-agent"), action="verify_success", success=True, message="ok")

    return ok({
        "valid": True,
        "expireAt": license_obj.expire_at,
        "plan": license_obj.plan,
        "productCode": license_obj.product_code,
    })
