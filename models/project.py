from database.db import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    user_associations = relationship("UserProject", back_populates="project")

    @property
    def users(self):
        result = []
        for assoc in self.user_associations:
            result.append(assoc.user)
        return result