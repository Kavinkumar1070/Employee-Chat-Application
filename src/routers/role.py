from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from src.core.utils import normalize_string
from src.core.authentication import roles_required
from src.core.database import get_db

from src.crud.role import *
from src.schemas.role import  RoleFunctionCreate,RoleFunctionUpdate

from src.schemas.role import(
                        Role,
                        UpdateRoleNameRequest,
                        EmployeeRole,
                        )

router = APIRouter(
    prefix="/roles",
    tags=["role"],
    responses={400: {"message": "Not found"}}
)


@router.post("", dependencies=[Depends(roles_required("admin"))])
async def create_role(name:Role,db:Session=Depends(get_db)):
    name=normalize_string(name.name)
    if create(db,name):
        return f"{name} Role Created Successfully"
    return {'message':f"{name} Role is Already Exists"}


@router.delete("/{id}", dependencies=[Depends(roles_required("admin"))])
async def delete_role(id:int, db: Session = Depends(get_db)):
    role=get(db,id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return delete(db, role.id)


@router.put("/{id}", dependencies=[Depends(roles_required("admin"))])
async def update_role(id: int, request: UpdateRoleNameRequest, db: Session = Depends(get_db)):
    exists_role=get(db,id)
    if exists_role:
        new_name=normalize_string(request.new_name)
        role =update(db, exists_role.id, new_name)
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Role updated")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")


@router.get("/{id}", dependencies=[Depends(roles_required("admin"))])
async def get_role(id:int,db:Session=Depends(get_db)):
    role=get(db,id)
    return role


@router.post("employee/role", dependencies=[Depends(roles_required("admin"))])
def assign_role_to_employee(data:EmployeeRole,db:Session=Depends(get_db)):
    data=assign_employee_role(db,data)
    if data:
        return data
    

# RoleFunction endpoints
@router.post("/{role_id}/functions/")
def create_new_role_function(role_id: int, role_function: RoleFunctionCreate, db: Session = Depends(get_db)):
    return create_role_function(db, role_function, role_id)

@router.get("/roles/{role_id}/functions/")
def read_role_functions(role_id: int, db: Session = Depends(get_db)): 
    return get_role_functions(db, role_id)

@router.delete("/roles/functions/{role_function_id}")
def delete_existing_role_function(role_function_id: int, db: Session = Depends(get_db)):
    db_role_function = delete_role_function(db, role_function_id)
    if db_role_function is None:
        raise HTTPException(status_code=404, detail="Role Function not found")
    return db_role_function
