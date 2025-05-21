from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from app import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from utils.get_db import get_db
from models.task import Task
from models.lane import Lane
from models.user import User
from models.project import Project
from typing import Annotated, Optional
from schemas.task import TaskCreate, TaskUpdate
from utils.auth import get_current_active_user

task = APIRouter()

@task.get("/empty")
async def empty(request: Request):
    return HTMLResponse(content="")

@task.patch("/{task_id}/position")
async def update_position(task_id: int, request: Request, new_index: Annotated[int, Form()], target_lane_id: Annotated[Optional[int], Form()] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    new_index = int(new_index)
    if target_lane_id and target_lane_id != "":
        target_lane_id = int(target_lane_id)
    task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    old_lane_id = task_obj.lane_id
    try:
        # 如果目標泳道的id和當前泳道id不同，任務會被移動到新的泳道
        if target_lane_id and target_lane_id != old_lane_id:
            # 驗證新泳道是否存在
            target_lane = db.query(Lane).filter(Lane.id == target_lane_id).first()
            if not target_lane:
                raise HTTPException(status_code=404, detail="目標泳道不存在。")
            # 更新舊泳道中的任務位置
            tasks_in_old_lane = db.query(Task).filter(Task.lane_id == old_lane_id, Task.id != task_id).order_by(Task.position).all()
            # 重新排序舊泳道中的任務
            for i, t in enumerate(tasks_in_old_lane, start=1):
                t.position = i
                db.add(t)
            # 取得新泳道中的任務
            tasks_in_new_lane = db.query(Task).filter(Task.lane_id == target_lane_id).order_by(Task.position).all()
            # 在新位置塞入任務
            for i, t in enumerate(tasks_in_new_lane):
                if i >= new_index:
                    t.position = i + 1
                    db.add(t)
            # 更新任務的泳道和位置
            task_obj.lane_id = target_lane_id
            task_obj.position = new_index
        else:
            # 在同一泳道內移動
            if old_lane_id:
                tasks = db.query(Task).filter(Task.lane_id == old_lane_id, Task.id != task_id).order_by(Task.position).all()
                # 塞入任務到新位置並更新其他任務位置
                tasks_to_update = []
                current_pos = 1
                for i, t in enumerate(tasks):
                    if current_pos == new_index:
                        current_pos += 1
                    t.position = current_pos
                    tasks_to_update.append(t)
                    current_pos += 1
                for t in tasks_to_update:
                    db.add(t)
                task_obj.position = new_index
        db.add(task_obj)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        print(f"更新任務位置時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新任務位置失敗: {str(e)}")

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
                error_content = templates.get_template("common/error_message.html").render({"message": "該泳道已存在此任務名稱"})
                return HTMLResponse(content=error_content, status_code=400)
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
        message_data = {
            "message": f"任務 {name} 建立成功。",
            "type": "success",
        }
        message_html = templates.get_template("common/message_data.html").render(message_data)
        if lane_id:
            tasks = db.query(Task).options(selectinload(Task.lane)).filter(Task.lane_id == lane_id).order_by(Task.position).all()
            tasks_html = templates.get_template("tasks/partials/lane_tasks.html").render({"request": request, "tasks": tasks, "current_user": current_user})
            return HTMLResponse(content=f"{message_html}{tasks_html}")
        else:
            tasks = db.query(Task).options(selectinload(Task.lane)).order_by(Task.position).all()
            content = templates.get_template("tasks/partials/tasks_list.html").render({"request": request, "tasks": tasks, "lane": None, "current_user": current_user})
            return HTMLResponse(content=f"{message_html}{content}")
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
    old_name = task_obj.name
    if lane_id:
        lane = db.query(Lane).filter(Lane.id == lane_id).first()
        if lane:
            project_id = lane.project_id
        existing_task = db.query(Task).filter(Task.name == update_data.name, Task.id != task_id, Task.lane_id == lane_id).first()
        if existing_task:
            if request.headers.get("HX-Request") == "true":
                error_content = templates.get_template("common/error_message.html").render({"message": "該泳道中已有相同名稱任務。"})
                return HTMLResponse(content=error_content, status_code=400)
            else:
                raise HTTPException(status_code=400, detail="該泳道中已有相同名稱任務。")
    task_obj.name = update_data.name
    db.commit()
    db.refresh(task_obj)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        if project_id:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.project_id == project_id).order_by(Lane.position).all()
            project = db.query(Project).filter(Project.id == project_id).first()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "project": project, "current_user": current_user})
        else:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).order_by(Lane.position).all()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "current_user": current_user})
        message_data = {
            "message": f"任務 {old_name} 已更新為 {name}。",
            "type": "success",
        }
        content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
        return HTMLResponse(content=content_message)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@task.get("/{task_id}/edit")
async def edit(request: Request, task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")
    project_id = None
    return_url = "/lanes"
    if task_obj.lane and task_obj.lane.project_id:
        project_id = task_obj.lane.project_id
        return_url = f"/lanes?project_id={project_id}"
    lanes = db.query(Lane).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("tasks/partials/tasks_edit.html").render({"request": request, "task": task_obj, "lanes": lanes, "project_id": project_id, "current_user": current_user, "return_url": return_url})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("tasks/edit.html", {"request": request, "task": task_obj, "lanes": lanes, "project_id": project_id, "current_user": current_user})

@task.post("/{task_id}/delete")
async def delete(task_id: int, request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    task_obj = db.query(Task).options(selectinload(Task.lane)).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="查無任務。")    
    task_name = task_obj.name
    project_id = None
    if task_obj.lane and task_obj.lane.project_id:
        project_id = task_obj.lane.project_id
    db.delete(task_obj)
    db.commit()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        if project_id:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.project_id == project_id).order_by(Lane.position).all()
            project = db.query(Project).filter(Project.id == project_id).first()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "project": project, "current_user": current_user})
        else:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).order_by(Lane.position).all()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "current_user": current_user})
        message_data = {
            "message": f"任務 {task_name} 已刪除。",
            "type": "success",
        }
        content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
        return HTMLResponse(content=content_message)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)