from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from utils.get_db import get_db
from models.project import Project
from models.lane import Lane
from models.user import User
from typing import Annotated, Optional
from schemas.project import ProjectCreate, ProjectUpdate
from utils.auth import get_current_active_user
from app import templates

project = APIRouter()

@project.get("/")
async def index(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.name.desc()).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_list.html").render({"request": request, "projects": projects, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("projects/index.html", {"request": request, "projects": projects, "current_user": current_user})

@project.post("/")
async def create(request: Request, name: Annotated[str, Form()], current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    create_data = ProjectCreate(name = name)
    projects = db.query(Project).filter(Project.name == create_data.name).first()
    if projects:
        raise HTTPException(status_code=400, detail="該專案名稱已被使用。")
    new_projects = Project(name = create_data.name)
    db.add(new_projects)
    db.commit()
    db.refresh(new_projects)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        projects = db.query(Project).order_by(Project.name.desc()).all()
        content = templates.get_template("projects/partials/projects_list.html").render({"projects": projects, "request": request})
        return HTMLResponse(content=content)
    else:
        return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)

@project.get("/new")
async def new(request: Request, current_user: User = Depends(get_current_active_user)):
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_form.html").render({"request": request})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("projects/new.html", {"request": request})

@project.post("/{project_name}/update")
async def update(project_name: str, name: Annotated[str, Form()], request: Request, description: Annotated[Optional[str], Form()] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    update_data = ProjectUpdate(name = name, description = description)
    projects = db.query(Project).filter(Project.name == project_name).first()
    if not projects:
        raise HTTPException(status_code=404, detail="查無專案。")
    existing_project = db.query(Project).filter(Project.name == update_data.name, Project.id != projects.id).first()
    if existing_project:
        if request.headers.get("HX-Request") == "true":
            return HTMLResponse(content=f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">該專案名稱已被使用</div>""",status_code=400)
        else:
            raise HTTPException(status_code=400, detail="該專案名稱已被使用。")
    projects.name = update_data.name
    if description is not None:
        projects.description = update_data.description
    db.commit()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_show.html").render({"request": request, "projects": projects, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)

@project.get("/{project_name}")
async def show(request: Request, project_name: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if not projects:
        raise HTTPException(status_code=404, detail="查無專案。")
    lanes = db.query(Lane).filter(Lane.project_id == projects.id).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_show.html").render({"request": request, "projects": projects, "lanes": lanes, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("projects/show.html", {"request": request, "projects": projects, "lanes": lanes, "current_user": current_user})

@project.get("/{project_name}/edit")
async def edit(request: Request, project_name: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if not projects:
        raise HTTPException(status_code=404, detail="查無專案名稱。")
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_edit.html").render({"request": request, "projects": projects, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("projects/edit.html", {"request": request, "projects": projects, "current_user": current_user})

@project.post("/{project_name}/delete")
async def delete(project_name: str, request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.name == project_name).first()
    if projects:
        db.delete(projects)
        db.commit()
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            projects = db.query(Project).order_by(Project.name.desc()).all()
            content = templates.get_template("projects/partials/projects_list.html").render({"projects": projects, "request": request})
            return HTMLResponse(content=content)
        else:
            return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)
    else:
        raise HTTPException(status_code=404, detail="查無專案。")