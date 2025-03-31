from pydantic import BaseModel, Field
from typing import Optional

class LaneCreate(BaseModel):
    name: str = Field(...)
    project_id: Optional[int] = None

class LaneUpdate(BaseModel):
    name: str = Field(...)