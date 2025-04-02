from database.db import DATABASE_URL, Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    project_associations = relationship("UserProject", back_populates="user")

    tasks = relationship("Task", back_populates="user")

    @property
    def projects(self):
        result = []
        for assoc in self.project_associations:
            result.append(assoc.project)
        return result