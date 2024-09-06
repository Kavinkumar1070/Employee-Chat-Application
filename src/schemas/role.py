from pydantic import BaseModel


class Role(BaseModel):
    name: str

    class Config:
        from_attributes = True


class UpdateRoleNameRequest(BaseModel):
    role_id: int
    new_name: str


class EmployeeRole(BaseModel):
    employee_id: str
    role_id: int


class RoleFunctionCreate(BaseModel):
    role_id: int
    function: str
    jsonfile: str


class RoleFunctionUpdate(BaseModel):
    function: str | None = None
    jsonfile: str | None = None
