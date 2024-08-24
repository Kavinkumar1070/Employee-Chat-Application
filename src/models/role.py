from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

from src.core.database import Base
from .association import employee_role

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    employees = relationship("EmployeeOnboarding", secondary=employee_role, back_populates="roles")
