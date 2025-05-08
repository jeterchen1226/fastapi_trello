from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from app import templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload
from utils.get_db import get_db
from models.lane import Lane
from models.user import User
from models.project import Project
from typing import Annotated, Optional
from schemas.lane import LaneCreate, LaneUpdate
from utils.auth import get_current_active_user

lane = APIRouter()

@lane.get("/")
async def index(request: Request, project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if project_id:
        lanes = db.query(Lane).options(selectinload(Lane.project), selectinload(Lane.tasks)).filter(Lane.project_id == project_id).all()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="查無專案。")
        return templates.TemplateResponse("lanes/index.html", {"request": request, "lanes": lanes, "project": project})
    else:
        lanes = db.query(Lane).options(selectinload(Lane.project)).all()
        return templates.TemplateResponse("lanes/index.html", {"request": request, "lanes": lanes})

@lane.post("/")
async def create(request: Request, name: Annotated[str, Form()], project_id: Annotated[Optional[int], Form()] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    create_data = LaneCreate(name=name, project_id=project_id)
    if project_id:
        lanes = db.query(Lane).filter(Lane.name == create_data.name, Lane.project_id == project_id).first()
        if lanes:
            raise HTTPException(status_code=400, detail="該專案中已存在此泳道名稱。")
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="查無專案。")
    new_lanes = Lane(name=create_data.name, project_id=project_id)
    db.add(new_lanes)
    db.commit()
    db.refresh(new_lanes)
    if project_id:
        return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@lane.get("/new")
async def new(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return templates.TemplateResponse("lanes/new.html", {"request": request, "projects": projects})

@lane.post("/{lane_id}/update")
async def update(lane_id: int, name: Annotated[str, Form()], current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    update_data = LaneUpdate(name=name)
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")
    project_id = lane.project_id
    existing_lane = db.query(Lane).filter(Lane.name == update_data.name, Lane.id != lane.id, Lane.project_id == project_id).first()
    if existing_lane:
        raise HTTPException(status_code=400, detail="該專案中已有相同名稱的泳道。")
    lane.name = update_data.name
    db.commit()
    if project_id:
        return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)    
    return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)

@lane.get("/{lane_id}")
async def show(request: Request, lane_id: int, project_id: Optional[int] = Query(None), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    query = db.query(Lane).options(selectinload(Lane.project)).filter(Lane.id == lane_id)
    if project_id:
        query = query.filter(Lane.project_id == project_id)
    lane = query.first()
    if lane:
        return templates.TemplateResponse("lanes/show.html", {"request": request, "lanes": lane})
    else:
        raise HTTPException(status_code=404, detail="查無泳道。")

@lane.get("/{lane_id}/edit")
async def edit(request: Request, lane_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if lane:
        projects = db.query(Project).all()
        if projects:
            project_id = lane.project_id
        else:
            project_id = None
        return templates.TemplateResponse("lanes/edit.html", {"request": request, "lanes": lane, "projects": projects, "project_id": project_id})
    else:
        raise HTTPException(status_code=404, detail="查無泳道。")

@lane.post("/{lane_id}/delete")
async def delete(lane_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    lane = db.query(Lane).options(selectinload(Lane.project)).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="查無泳道。")    
    project_id = lane.project_id
    db.delete(lane)
    db.commit()
    if project_id:
        return RedirectResponse(url=f"/lanes?project_id={project_id}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/lanes", status_code=status.HTTP_302_FOUND)