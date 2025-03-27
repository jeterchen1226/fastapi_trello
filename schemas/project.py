# app/projects/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="專案名稱")

class ProjectUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="專案名稱")
    description: Optional[str] = Field(None, max_length=500, description="專案描述")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('專案名稱不能為空白')
        return v.strip()