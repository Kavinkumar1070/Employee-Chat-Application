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

class RoleFunctionCreate(BaseModel):
    function: str
    jsonfile: str

class RoleFunctionUpdate(BaseModel):
    function: str |None=None
    jsonfile: str |None=None
