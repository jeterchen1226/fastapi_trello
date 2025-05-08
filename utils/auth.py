from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from models.user import User
from utils.get_db import get_db
from fastapi import Request
import os

# 密碼加密設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 設定
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
# 1 天
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# OAuth2 設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login", auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="身份驗證無效。", headers={"WWW-Authenticate": "Bearer"},)
    token = get_token_from_cookie(request)
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(request: Request = None, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="使用者已停用。")
    return current_user

def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        return token.replace("Bearer ", "")
    return None