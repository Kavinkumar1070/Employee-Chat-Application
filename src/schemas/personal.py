from pydantic import BaseModel,Field
from typing import Optional
from datetime import date

class EmployeeBase(BaseModel):
    FirstName: str
    LastName: str
    DateOfBirth: date = Field(..., example="1990-05-15") 
    ContactNumber: str
    EmailAddress: str
    Address: str
    Nationality: str
    Gender: str
    MaritalStatus: str

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    FirstName: str |None=None
    LastName: str |None=None
    DateOfBirth: date = Field(None, example="1990-05-15")  
    ContactNumber: str |None=None
    EmailAddress: str |None=None
    Address: str |None=None
    Nationality: str |None=None
    Gender: str |None=None
    MaritalStatus: str |None=None