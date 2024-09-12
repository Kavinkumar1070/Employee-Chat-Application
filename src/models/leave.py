from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Enum,
    Text,
    TIMESTAMP,
    DateTime,
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy.sql import func
from src.core.database import Base

class LeaveDuration(PyEnum):
    ONE_DAY = "oneday"
    HALF_DAY = "halfday"


class LeaveStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EmployeeLeave(Base):
    __tablename__ = "employee_leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employee_employment_details.id"), nullable=False
    )
    leave_type = Column(String(50), nullable=False)
    duration = Column(
        Enum(LeaveDuration), default=LeaveDuration.ONE_DAY, nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    employee = relationship("EmployeeEmploymentDetails", back_populates="leaves")


class LeaveCalendar(Base):
    __tablename__ = "leavecalendar"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee_employment_details.id"), unique=True, index=True)
    sick_leave = Column(Integer, default=0)
    personal_leave = Column(Integer, default=0)
    vacation_leave = Column(Integer, default=0)
    unpaid_leave = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    employee = relationship("EmployeeEmploymentDetails", back_populates="leave_calendar")