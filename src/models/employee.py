
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DECIMAL, Boolean, func
from sqlalchemy.orm import relationship
from src.core.database import Base
from sqlalchemy.orm import validates
from datetime import date

class EmployeeEmploymentDetails(Base):
    __tablename__ = 'employee_employment_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employment_id = Column(String(100), unique=True, nullable=False)
    job_position = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    employment_type = Column(String(50), nullable=False)
    reporting_manager = Column(String(100))
    work_location = Column(String(100))
    basic_salary = Column(DECIMAL(10, 2))
    is_active = Column(Boolean, nullable=False, default=True)
    releave_date = Column(Date, default=None)

    employee_id = Column(Integer, ForeignKey('employee_onboarding.id'))
    employee = relationship("EmployeeOnboarding", back_populates="employment_details")

    @validates('is_active')
    def validate_is_active(self, key, value):
        if not value:
            self.releave_date = date.today()
        return value
