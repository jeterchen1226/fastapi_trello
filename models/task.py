from database.db import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tasks")
    lane_id = Column(Integer, ForeignKey("lanes.id"))
    lane = relationship("Lane", back_populates="tasks")
    name = Column(String, nullable=False)
    priority = Column(String, nullable=True)
    status = Column(String, nullable=True)
    end_date = Column(DateTime)
    position = Column(Integer)
