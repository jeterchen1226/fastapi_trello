from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from utils.auth import SECRET_KEY, ALGORITHM
import re

# 不需要身份驗證的路徑
PUBLIC_PATHS = [
    re.compile(r"^/$"),
    re.compile(r"^/users/login/?$"),
    re.compile(r"^/users/register/?$"),
    re.compile(r"^/static/.*$"),
]

async def auth_middleware(request: Request, call_next):
    # 檢查是否為公開路徑
    path = request.url.path
    if any(pattern.match(path) for pattern in PUBLIC_PATHS):
        return await call_next(request)
    # 檢查 Cookie 中的 access_token
    access_token = request.cookies.get("access_token")
    if not access_token or not access_token.startswith("Bearer "):
        print("No valid token found in cookie, redirecting to login")
        return RedirectResponse(url="/users/login", status_code=status.HTTP_302_FOUND)
    token = access_token.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token decoded successfully: sub={payload.get('sub')}")
    except JWTError as e:
        print(f"Token decode error: {str(e)}")
        return RedirectResponse(url="/users/login", status_code=status.HTTP_302_FOUND)
    return await call_next(request)