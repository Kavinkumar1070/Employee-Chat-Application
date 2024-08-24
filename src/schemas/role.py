from pydantic import BaseModel
from typing import List



class Role(BaseModel):
    name: str

    class Config:
        from_attributes = True


class UpdateRoleNameRequest(BaseModel):
    new_name: str


class EmployeeRole(BaseModel):
    employee_id:str
    role_id:int