from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class EmployeeOnboarding(Base):
    __tablename__ = 'employee_onboarding'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    DateOfBirth = Column(Date, nullable=False)
    ContactNumber = Column(String(15), nullable=False)
    EmailAddress = Column(String(100), nullable=False)
    Address = Column(Text, nullable=False)
    Nationality = Column(String(50), nullable=False)
    Gender = Column(String(10))
    MaritalStatus = Column(String(50))

    employment_details = relationship("EmployeeEmploymentDetails", back_populates="employee") 
