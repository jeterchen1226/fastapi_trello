from database.db import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class UserProject(Base):
    __tablename__ = "user_projects"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)

    user = relationship("User", back_populates="project_associations")
    project = relationship("Project", back_populates="user_associations")