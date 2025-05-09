from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from app import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from utils.get_db import get_db
from models.task import Task
from models.lane import Lane
from models.user import User
from typing import Annotated, Optional
from schemas.task import TaskCreate, TaskUpdate
from utils.auth import get_current_active_user

task = APIRouter()

@task.get("/")
async def index(request: Request, lane_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if lane_id:
        tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.lane_id == lane_id).order_by(Task.position).all()
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if not lane:
            raise HTTPException(status_code=404, detail="查無泳道。")
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            content = templates.get_template("tasks/partials/tasks_list.html").render({"request": request, "tasks": tasks, "lane": lane, "project_id": lane.project_id, "current_user": current_user})
            return HTMLResponse(content=content)
        else:
            return templates.TemplateResponse("tasks/index.html", {"request": request, "tasks": tasks, "lane": lane, "project_id": lane.project_id, "current_user": current_user})
    else:
        tasks = db.query(Task).options(selectinload(Task.lane)).order_by(Task.position).all()
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            content = templates.get_template("tasks/partials/tasks_list.html").render({"request": request, "tasks": tasks, "lane": None, "current_user": current_user})
            return HTMLResponse(content=content)
        else:
            return templates.TemplateResponse("tasks/index.html", {"request": request, "tasks": tasks, "lane": None, "current_user": current_user})

@task.post("/")
async def create(request: Request, name: Annotated[str, Form()], lane_id: Annotated[Optional[int], Form()] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    create_data = TaskCreate(name=name, lane_id=lane_id)
    project_id = None
    if lane_id:
        existing_task = db.query(Task).filter(Task.name == create_data.name, Task.lane_id == lane_id).first()
        if existing_task:
            if request.headers.get("HX-Request") == "true":
                return HTMLResponse(content=f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">該泳道已存在此任務名稱</div>""", status_code=400)
            else:
                raise HTTPException(status_code=400, detail="該泳道已存在此任務名稱。")
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if not lane:
            raise HTTPException(status_code=404, detail="查無泳道。")
        project_id = lane.project_id
    if lane_id:
        max_position = db.query(func.max(Task.position)).filter(Task.lane_id == lane_id).scalar() or 0
    else:
        max_position = db.query(func.max(Task.position)).scalar() or 0
    new_task = Task(name=create_data.name, lane_id=lane_id, position=max_position + 1)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        if lane_id:
            tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.lane_id == lane_id).order_by(Task.position).all()
            content = templates.get_template("tasks/partials/tasks_item.html").render({"request": request, "tasks": tasks, "current_user": current_user})
        else:
            tasks = db.query(Task).options(selectinload(Task.lane)).order_by(Task.position).all()
            content = templates.get_template("tasks/partials/tasks_list.html").render({"request": request, "tasks": tasks, "lane": None, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@task.get("/new")
async def new(request: Request, lane_id: Optional[int] = Query(None), project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    lane = None
    lanes = []
    if lane_id:
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if not lane:
            raise HTTPException(status_code=404, detail="查無泳道。")
    else:
        lanes = db.query(Lane).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("tasks/partials/tasks_form.html").render({"request": request, "lane": lane, "lanes": lanes, "project_id": project_id, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("tasks/new.html", {"request": request, "lane": lane, "project_id": project_id, "current_user": current_user})

@task.post("/{task_id}/update")
async def update(task_id: int, name: Annotated[str, Form()], request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    update_data = TaskUpdate(name=name)
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    lane_id = task_obj.lane_id
    project_id = None
    if lane_id:
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if lane:
            project_id = lane.project_id
        existing_task = db.query(Task).filter(Task.name == update_data.name, Task.id != task_id, Task.lane_id == lane_id).first()
        if existing_task:
            if request.headers.get("HX-Request") == "true":
                return HTMLResponse(content=f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">該泳道中已有相同名稱任務</div>""", status_code=400)
            else:
                # 非HTMX請求，拋出異常
                raise HTTPException(status_code=400, detail="該泳道中已有相同名稱任務。")
    task_obj.name = update_data.name
    db.commit()
    db.refresh(task_obj)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("tasks/partials/tasks_show.html").render({"request": request, "task": task_obj, "project_id": project_id, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@task.get("/{task_id}")
async def show(request: Request, task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    project_id = None
    if task_obj.lane and task_obj.lane.project_id:
        project_id = task_obj.lane.project_id
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("tasks/partials/tasks_show.html").render({"request": request, "task": task_obj, "project_id": project_id, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("tasks/show.html", {"request": request, "task": task_obj, "project_id": project_id, "current_user": current_user})

@task.get("/{task_id}/edit")
async def edit(request: Request, task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    project_id = None
    if task_obj.lane and task_obj.lane.project_id:
        project_id = task_obj.lane.project_id
    lanes = db.query(Lane).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("tasks/partials/tasks_edit.html").render({"request": request, "task": task_obj, "lanes": lanes, "project_id": project_id, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("tasks/edit.html", {"request": request, "task": task_obj, "lanes": lanes, "project_id": project_id, "current_user": current_user})

@task.post("/{task_id}/delete")
async def delete(task_id: int, request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    lane_id = task_obj.lane_id
    project_id = None
    if task_obj.lane and task_obj.lane.project_id:
        project_id = task_obj.lane.project_id
    db.delete(task_obj)
    db.commit()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        if lane_id:
            tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.lane_id == lane_id).order_by(Task.position).all()
            lane = db.query(Lane).filter(Lane.id == lane_id).first()
            response_content = templates.get_template("tasks/partials/tasks_list.html").render({"request": request, "tasks": tasks, "lane": lane, "project_id": project_id, "current_user": current_user})
            return HTMLResponse(content=response_content, headers={"HX-Redirect": f"/lanes?project_id={project_id}" if project_id else "/lanes"})
        else:
            return HTMLResponse(content="", headers={"HX-Redirect": f"/lanes?project_id={project_id}" if project_id else "/lanes"})
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)