from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from app import templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload
from utils.get_db import get_db
from models.project import Project
from models.lane import Lane
from typing import Annotated, Optional
from schemas.project import ProjectCreate, ProjectUpdate

project = APIRouter()

@project.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.name.desc()).all()
    return templates.TemplateResponse("projects/index.html", {"request": request, "projects": projects})

@project.post("/")
def create(request: Request, name: Annotated[str, Form()], db: Session = Depends(get_db)):
    create_data = ProjectCreate(name = name)
    projects = db.query(Project).filter(Project.name == create_data.name).first()
    if projects:
        raise HTTPException(status_code=400, detail="該專案名稱已被使用。")
    new_projects = Project(name = create_data.name)
    db.add(new_projects)
    db.commit()
    db.refresh(new_projects)
    return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)

@project.get("/new")
def new(request: Request):
    return templates.TemplateResponse("projects/index.html", {"request": request})

@project.post("/{project_name}/update")
def update(project_name: str, name: Annotated[str, Form()], description: Annotated[Optional[str], Form()] = None, db: Session = Depends(get_db)):
    update_data = ProjectUpdate(name = name, description = description)
    projects = db.query(Project).filter(Project.name == project_name).first()
    if not projects:
        raise HTTPException(status_code=404, detail="查無專案。")
    existing_project = db.query(Project).filter(Project.name == update_data.name, Project.id != projects.id).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="該專案名稱已被使用。")
    projects.name = update_data.name
    if description is not None:
        projects.description = update_data.description
    db.commit()
    return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)

@project.get("/{project_name}")
def show(request: Request, project_name: str, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if not projects:
        raise HTTPException(status_code=404, detail="查無專案。")
    lanes = db.query(Lane).filter(Lane.project_id == projects.id).all()
    return templates.TemplateResponse("projects/show.html", {"request": request, "projects": projects, "lanes": lanes})

@project.get("/{project_name}/edit")
def edit(request: Request, project_name: str, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if projects:
        return templates.TemplateResponse("projects/edit.html", {"request": request, "projects": projects})
    else:
        raise HTTPException(status_code=404, detail="查無專案名稱。")

@project.post("/{project_name}/delete")
def delete(project_name: str, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if projects:
        db.delete(projects)
        db.commit()
        return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)
    else:
        raise HTTPException(status_code=404, detail="查無專案。")