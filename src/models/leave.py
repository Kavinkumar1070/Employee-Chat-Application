from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy.sql import func
from src.core.database import Base

class LeaveDuration(PyEnum):
    ONE_DAY = "one_day"
    HALF_DAY = "half_day"

class LeaveStatus(PyEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class EmployeeLeave(Base):
    __tablename__ = "employee_leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('employee_employment_details.id'), nullable=False)
    leave_type = Column(String(50), nullable=False)
    duration = Column(Enum(LeaveDuration),default=LeaveDuration.ONE_DAY, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)

    employee = relationship("EmployeeEmploymentDetails", back_populates="leaves")
