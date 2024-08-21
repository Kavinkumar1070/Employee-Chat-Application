
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DECIMAL, Boolean, func,DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base
from sqlalchemy.orm import validates
from datetime import date,datetime

class EmployeeEmploymentDetails(Base):
    __tablename__ = 'employee_employment_details'

    employment_id = Column(String(100), primary_key=True)
    employee_email = Column(String(100), unique=True)
    job_position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    employment_type = Column(String(50), nullable=False)
    reporting_manager = Column(String(100))
    work_location = Column(String(100))
    basic_salary = Column(DECIMAL(10, 2))
    releave_date = Column(Date, default=None)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee_id = Column(Integer, ForeignKey('employee_onboarding.id'))
    employee = relationship("EmployeeOnboarding", back_populates="employment_details")

    @validates('is_active')
    def validate_is_active(self, key, value):
        if not value:
            self.releave_date = date.today()
        return value
