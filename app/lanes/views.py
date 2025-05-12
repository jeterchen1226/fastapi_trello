from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from app import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload
from utils.get_db import get_db
from models.lane import Lane
from models.user import User
from models.project import Project
from models.task import Task
from typing import Annotated, Optional
from schemas.lane import LaneCreate, LaneUpdate
from utils.auth import get_current_active_user
from sqlalchemy import func

lane = APIRouter()

# 初始化所有泳道的位置值
@lane.get("/initialize-positions")
async def initialize_positions(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    for project in projects:
        lanes = db.query(Lane).filter(Lane.project_id == project.id).order_by(Lane.id).all()
        for i, lane in enumerate(lanes, start=1):
            lane.position = i
            db.add(lane)
    no_project_lanes = db.query(Lane).filter(Lane.project_id == None).order_by(Lane.id).all()
    for i, lane in enumerate(no_project_lanes, start=1):
        lane.position = i
        db.add(lane)
    db.commit()
    
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        message_data = {
            "message": "所有泳道位置已初始化成功。",
            "type": "success",
        }
        return HTMLResponse(content=f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>""")
    return {"message": "所有泳道位置已初始化成功。"}

@lane.get("/")
async def index(request: Request, project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if project_id:
        lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.project_id == project_id).order_by(Lane.position).all()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="查無專案。")
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "project": project, "current_user": current_user})
            return HTMLResponse(content=content)
        else:
            return templates.TemplateResponse("lanes/index.html", {"request": request, "lanes": lanes, "project": project, "current_user": current_user})
    else:
        lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).order_by(Lane.position).all()
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "current_user": current_user})
            return HTMLResponse(content=content)
        else:
            return templates.TemplateResponse("lanes/index.html", {"request": request, "lanes": lanes, "current_user": current_user})

@lane.post("/")
async def create(request: Request, name: Annotated[str, Form()], project_id: Annotated[Optional[int], Form()] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    create_data = LaneCreate(name=name, project_id=project_id)
    if project_id:
        lanes = db.query(Lane).filter(Lane.name == create_data.name, Lane.project_id == project_id).first()
        if lanes:
            if request.headers.get("HX-Request") == "true":
                return HTMLResponse(content=f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">該專案中已存在此泳道名稱</div>""",status_code=400)
            else:
                raise HTTPException(status_code=400, detail="該專案中已存在此泳道名稱。")
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="查無專案。")
    if project_id:
        max_position = db.query(func.max(Lane.position)).filter(Lane.project_id == project_id).scalar() or 0
    else:
        max_position = db.query(func.max(Lane.position)).scalar() or 0
    new_lanes = Lane(name=create_data.name, project_id=project_id, position=max_position + 1)
    db.add(new_lanes)
    db.commit()
    db.refresh(new_lanes)
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        if project_id:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.project_id == project_id).order_by(Lane.position).all()
            project = db.query(Project).filter(Project.id == project_id).first()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "project": project, "current_user": current_user})
            message_data = {
                "message": f"泳道 {name} 建立成功。",
                "type": "success",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
            return HTMLResponse(content=content_message)
        else:
            lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).order_by(Lane.position).all()
            content = templates.get_template("lanes/partials/lanes_list.html").render({"request": request, "lanes": lanes, "current_user": current_user})
            message_data = {
                "message": f"泳道 {name} 建立成功。",
                "type": "success",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
            return HTMLResponse(content=content_message)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@lane.get("/new")
async def new(request: Request, project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    project = None
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("lanes/partials/lanes_form.html").render({"request": request, "projects": projects, "project": project, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("lanes/new.html", {"request": request, "projects": projects, "project": project, "current_user": current_user})

@lane.post("/{lane_id}/update")
async def update(lane_id: int, name: Annotated[str, Form()], request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    update_data = LaneUpdate(name=name)
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")
    project_id = lane.project_id
    existing_lane = db.query(Lane).filter(Lane.name == update_data.name, Lane.id != lane.id, Lane.project_id == project_id).first()
    if existing_lane:
        if request.headers.get("HX-Request") == "true":
            error_content = f"""<div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">已有同名泳道</div>"""
            message_data = {
                "message": "已經有相同泳道存在。",
                "type": "error",
            }
            content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{error_content}"""
            return HTMLResponse(content=content_message, status_code=400)
        else:
            raise HTTPException(status_code=400, detail="該專案中已有相同名稱的泳道。")
    lane.name = update_data.name
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
            "message": f"泳道 {name} 更新成功。",
            "type": "success",
        }
        content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
        return HTMLResponse(content=content_message)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)    
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@lane.get("/{lane_id}")
async def show(request: Request, lane_id: int, project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    query = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.id == lane_id)
    if project_id:
        query = query.filter(Lane.project_id == project_id)
    lane = query.first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("lanes/partials/lane_detail.html").render({"request": request, "lanes": lane, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("lanes/show.html", {"request": request, "lanes": lane, "current_user": current_user})

@lane.get("/{lane_id}/edit")
async def edit(request: Request, lane_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")
    projects = db.query(Project).all()
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        content = templates.get_template("lanes/partials/lanes_edit.html").render({"request": request, "lanes": lane, "projects": projects, "current_user": current_user})
        return HTMLResponse(content=content)
    else:
        return templates.TemplateResponse("lanes/edit.html", {"request": request, "lanes": lane, "projects": projects, "current_user": current_user})

@lane.post("/{lane_id}/delete")
async def delete(lane_id: int, request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    lane = db.query(Lane).options(selectinload(Lane.project)).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")    
    project_id = lane.project_id
    lane_name = lane.name
    db.delete(lane)
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
            "message": f"泳道 {lane_name} 刪除成功。",
            "type": "success",
        }
        content_message = f"""<div id="message-data" style="display:none;" data-message="{message_data['message']}" data-type="{message_data['type']}"></div>{content}"""
        return HTMLResponse(content=content_message)
    else:
        if project_id:
            return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)