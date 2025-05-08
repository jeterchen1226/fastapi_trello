from fastapi import Depends, Query, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from database.db import Base, engine
from utils.get_db import get_db
from app import app
from app.users.views import user as user_route
from app.projects.views import project as project_route
from app.lanes.views import lane as lane_routes
from app.tasks.views import task as task_routes
from fastapi.staticfiles import StaticFiles
from middleware import auth_middleware
from fastapi.responses import RedirectResponse

app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

app.include_router(user_route, prefix="/users")
app.include_router(project_route, prefix="/projects")
app.include_router(lane_routes, prefix="/lanes")
app.include_router(task_routes, prefix="/tasks")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return RedirectResponse(url="/users/login")

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).fetchone()
        return {"message": "success"}
    except Exception as e:
        return {"message": "error", "e": e}

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)