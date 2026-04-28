from fastapi.responses import JSONResponse


def ok(data=None, msg="ok"):
    return {"code": 0, "msg": msg, "data": data or {}}


def fail(msg="error", code=400, data=None):
    return JSONResponse(
        status_code=code,
        content={"code": code, "msg": msg, "data": data or {}},
    )
