from database.db import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

class Lane(Base):
    __tablename__ = "lanes"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)

    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="lanes")