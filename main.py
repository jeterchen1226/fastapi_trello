from fastapi import FastAPI, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.db import Base, engine
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from utils.get_db import get_db
from app import app
from app.users.views import user as user_route
from models.user import User

app.include_router(user_route, prefix="/users")

@app.get("/")
def index():
    return {"message": "hello world"}

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).fetchone()
        return {"message": "success"}
    except Exception as e:
        return {"message": "error", "e": e}

@app.get("/test/{test_id}")
def test(test_id: str):
    return {"test_id": test_id}

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