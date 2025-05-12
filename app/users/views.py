from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from datetime import timedelta
from app import templates
from utils.get_db import get_db
from utils.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models.user import User
import urllib.parse

user = APIRouter()

@user.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@user.post("/register")
def register(request: Request, name: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()], password_confirmation: Annotated[str, Form()], db: Session = Depends(get_db)):
    if password != password_confirmation:
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "密碼與確認密碼不匹配"}, status_code=400)
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "該郵箱已被註冊"}, status_code=400)
    hashed_password = get_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)
    encoded_name = urllib.parse.quote(name)
    response = RedirectResponse(url=f"/projects?register=success&name={encoded_name}", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@user.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@user.post("/login")
async def login(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "無效的電子郵件或密碼"}, status_code=400)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    response = RedirectResponse(url=f"/projects?login=success&name={urllib.parse.quote(user.name)}", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@user.get("/logout")
def logout():
    response = RedirectResponse(url="/users/login?logout=success", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@user.get("/")
async def index(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    users = db.query(User).all()
    return templates.TemplateResponse("users/index.html", {"request": request, "users": users})

@user.post("/")
async def create(request: Request, name: Annotated[str, Form()], password: Annotated[str, Form()], email: Annotated[str, Form()], db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="電子郵件已被註冊")
    
    hashed_password = get_password_hash(password)
    new_user = User(name=name, password=hashed_password, email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    users = db.query(User).all()
    return templates.TemplateResponse("users/index.html", {"request": request, "users": users})

@user.get("/new")
async def new(request: Request, current_user: User = Depends(get_current_active_user)):
    return templates.TemplateResponse("users/index.html", {"request": request})

@user.post("/{user_id}/update")
async def update(user_id: int, name: Annotated[str, Form()], email: Annotated[str, Form()], db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.name = name
        user.email = email
        db.commit()
        return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_302_FOUND)
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.get("/{user_id}")
async def show(request: Request, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return templates.TemplateResponse("users/show.html", {"request": request, "user": user})
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.get("/{user_id}/edit")
async def edit(request: Request, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return templates.TemplateResponse("users/edit.html", {"request": request, "user": user})
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.post("/{user_id}/delete")
async def delete(request: Request, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)