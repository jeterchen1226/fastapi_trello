from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from app import templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload
from utils.get_db import get_db
from models.task import Task
from models.lane import Lane
from typing import Annotated, Optional
from schemas.task import TaskCreate, TaskUpdate

task = APIRouter()

@task.get("/")
def index(request: Request, lane_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if lane_id:
        tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.lane_id == lane_id).all()
        lanes = db.query(Lane).filter(Lane.id == lane_id).first()
        if not lanes:
            raise HTTPException(status_code=404, detail="查無泳道。")
        return templates.TemplateResponse("tasks/index.html", {"request": request, "tasks": tasks, "lanes": lanes})
    else:
        tasks = db.query(Task).options(selectinload(Task.lane)).all()
        return templates.TemplateResponse("tasks/index.html", {"request": request, "tasks": tasks, "lane": None})

@task.post("/")
def create(name: Annotated[str, Form()], lane_id: Annotated[Optional[int], Form()] = None, db: Session = Depends(get_db)):
    create_data = TaskCreate(name=name, lane_id=lane_id)
    if lane_id:
        existing_task = db.query(Task).filter(Task.name == create_data.name, Task.lane_id == lane_id).first()
        if existing_task:
            raise HTTPException(status_code=400, detail="該泳道已存在此任務名稱。")
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if not lane:
            raise HTTPException(status_code=404, detail="查無泳道。")
        project_id = lane.project_id
    else:
        lane = None
        project_id = None
    new_task = Task(name=create_data.name, lane_id=lane_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    if project_id:
        return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@task.get("/new")
def new(request: Request, lane_id: Optional[int] = Query(None), project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    lane = None
    tasks = []
    if lane_id:
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if lane:
            tasks = lane.tasks
        else:
            raise HTTPException(status_code=404, detail="查無泳道。")
    return templates.TemplateResponse("tasks/index.html", {"request": request, "lane": lane, "project_id": project_id,"tasks": tasks})

@task.get("/{task_id}")
def show(request: Request, task_id: int, lane_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id)
    if lane_id:
        query = query.filter(Task.lane_id == lane_id).first()
        if query:
            return templates.TemplateResponse("tasks/show.html", {"request": request, "tasks": query})
        else:
            raise HTTPException(status_code=404, detail="查無任務。")

@task.post("/{task_id}/update")
def update(task_id: int, name: Annotated[str, Form()], db: Session = Depends(get_db)):
    update_data = TaskUpdate(name=name)
    tasks = db.query(Task).filter(Task.id == task_id).first()
    if not tasks:
        raise HTTPException(status_code=404, detail="查無任務。")
    lane_id = tasks.lane_id
    existing_task = db.query(Task).filter(Task.name == update_data.name, Task.id != tasks.id, Task.lane_id == lane_id).first()
    if existing_task:
        raise HTTPException(status_code=400, detail="該泳道中已有相同名稱任務。")
    tasks.name = update_data.name
    db.commit()
    if lane_id:
        return RedirectResponse(url=f"/tasks?lane_id={lane_id}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

@task.get("/{task_id}/edit")
def edit(request: Request, task_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.id == task_id).first()
    if tasks:
        lanes = db.query(Lane).all()
        return templates.TemplateResponse("tasks/edit.html", {"request": request, "tasks": tasks, "lanes": lanes})
    else:
        raise HTTPException(status_code=404, detail="查無任務。")

@task.post("/{task_id}/delete")
def delete(task_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not tasks:
        raise HTTPException(status_code=404, detail="查無任務。")
    lane_id = tasks.lane_id
    db.delete(tasks)
    db.commit()
    if lane_id:
        return RedirectResponse(url=f"/tasks?lane_id={lane_id}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)