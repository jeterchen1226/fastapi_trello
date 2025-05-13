from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from utils.get_db import get_db
from models.project import Project
from models.lane import Lane
from models.user import User
from models.user_project import UserProject
from typing import Annotated, Optional
from schemas.project import ProjectCreate, ProjectUpdate
from utils.auth import get_current_active_user
from app import templates
from utils.flash import get_flash_message

project = APIRouter()

@project.get("/")
async def index(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id).order_by(Project.name.desc()).all()
    flash_category, flash_message = get_flash_message(request)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("projects/partials/projects_list.html").render({"request": request, "projects": projects, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("projects/index.html", {"request": request, "projects": projects, "current_user": current_user, "flash_category": flash_category, "flash_message": flash_message})

@project.post("/")
async def create(request: Request, name: Annotated[str, Form()], current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    create_data = ProjectCreate(name = name)
    project = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == create_data.name).first()
    is_htmx = request.headers.get("HX-Request") == "true"
    if project:
        if is_htmx:
            error_content = f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">您已有同名專案</div>"""
            message_data = {
                "message": "您已經建立過相同名稱的專案。",
                "type": "error",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{error_content}"""
            return HTMLResponse(content=content_message, status_code=400)
        else:
            raise HTTPException(status_code=400, detail="您已經建立過相同名稱的專案。")
    new_projects = Project(name = create_data.name)
    db.add(new_projects)
    db.commit()
    db.refresh(new_projects)
    user_project = UserProject(user_id = current_user.id, project_id = new_projects.id)
    db.add(user_project)
    db.commit()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        projects = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id).order_by(Project.name.desc()).all()
        content = templates.get_template("projects/partials/projects_list.html").render({"projects": projects, "request": request, "current_user": current_user})
        message_data = {
            "message": f"專案 {name} 建立成功。",
            "type": "success",
        }
        content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
        return HTMLResponse(content=content_message)
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
    project = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail="查無專案。")
    existing_project = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == update_data.name, Project.id != project.id).first()
    if existing_project:
        if request.headers.get("HX-Request") == "true":
            error_content = f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">您已有同名專案</div>"""
            message_data = {
                "message": "您已經建立過相同名稱的專案。",
                "type": "error",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{error_content}"""
            return HTMLResponse(content=content_message, status_code=400)
        else:
            raise HTTPException(status_code=400, detail="您已經建立過相同名稱的專案。")
    try:
        project.name = update_data.name
        if description is not None:
            project.description = update_data.description
        db.commit()
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            content = templates.get_template("projects/partials/projects_show.html").render({"request": request, "projects": project, "current_user": current_user})
            message_data = {
                "message": "編輯成功。",
                "type": "success",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
            return HTMLResponse(content=content_message)
        else:
            return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        db.rollback()
        print(f"更新專案時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新專案時發生錯誤: {str(e)}")

@project.get("/{project_name}")
async def show(request: Request, project_name: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == project_name).order_by(Project.name.desc()).first()
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
    projects = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == project_name).order_by(Project.name.desc()).first()
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
    proj = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id, Project.name == project_name).first()
    if proj:
        try:
            db.query(UserProject).filter(UserProject.project_id == proj.id).delete()
            db.delete(proj)
            db.commit()
            is_htmx = request.headers.get("HX-Request") == "true"
            if is_htmx:
                projects = db.query(Project).join(UserProject, UserProject.project_id == Project.id).filter(UserProject.user_id == current_user.id).order_by(Project.name.desc()).all()
                content = templates.get_template("projects/partials/projects_list.html").render({"projects": projects, "request": request, "current_user": current_user})
                message_data = {
                    "message": f"專案 {project_name} 已刪除成功。",
                    "type": "success",
                }
                content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
                return HTMLResponse(content=content_message)
            else:
                return RedirectResponse(url="/projects", status_code=status.HTTP_302_FOUND)
        except Exception as e:
            db.rollback()
            print(f"刪除專案時發生錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=f"刪除專案時發生錯誤: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="查無專案。")