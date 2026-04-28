from app.database import ActivationLog, now_ts


def write_log(db, *, license_id=None, license_key=None, machine_fingerprint=None, ip=None, user_agent=None, action="unknown", success=False, message=""):
    item = ActivationLog(
        license_id=license_id,
        license_key=license_key,
        machine_fingerprint=machine_fingerprint,
        ip=ip,
        user_agent=user_agent,
        action=action,
        success=1 if success else 0,
        message=message,
        created_at=now_ts(),
    )
    db.add(item)
    db.commit()
