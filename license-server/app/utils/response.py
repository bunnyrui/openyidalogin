def ok(data=None, msg="ok"):
    return {"code": 0, "msg": msg, "data": data or {}}


def fail(msg="error", code=400, data=None):
    return {"code": code, "msg": msg, "data": data or {}}
