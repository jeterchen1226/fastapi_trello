from pydantic import BaseModel, Field
from typing import Optional

class TaskCreate(BaseModel):
    name: str = Field(...)
    user_id: Optional[int] = None
    lane_id: Optional[int] = None

class TaskUpdate(BaseModel):
    name: str = Field(...)