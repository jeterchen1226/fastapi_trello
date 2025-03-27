from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from app import templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from utils.get_db import get_db
from models.user import User
from typing import Annotated

user = APIRouter()

@user.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("users/index.html", {"request": request, "users": users})

@user.post("/")
def create(request: Request, name: Annotated[str, Form()], password: Annotated[str, Form()], email: Annotated[str, Form()], db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="電子郵件已被註冊")
    new_user = User(name = name, password = password, email = email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    users = db.query(User).all()
    return templates.TemplateResponse("users/index.html", {"request": request, "users": users})

@user.get("/new")
def new(request: Request):
    return templates.TemplateResponse("users/index.html", {"request": request})

@user.post("/{user_id}/update")
def update(user_id: int, name: Annotated[str, Form()], email: Annotated[str, Form()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.name = name
        user.email = email
        db.commit()
        return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_302_FOUND)
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.get("/{user_id}")
def show(request: Request, user_id = int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return templates.TemplateResponse("users/show.html", {"request": request, "user": user})
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.get("/{user_id}/edit")
def edit(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return templates.TemplateResponse("users/edit.html", {"request": request, "user": user})
    else:
        raise HTTPException(status_code=404, detail="查無使用者")

@user.post("/{user_id}/delete")
def delete(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)