from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from src.core.utils import normalize_string
from src.core.authentication import roles_required
from src.core.database import get_db

from src.schemas.role import(
                        Role,
                        UpdateRoleNameRequest,
                        EmployeeRole,
                        )
from src.crud.role import(
                        get,
                        create,
                        delete,
                        update,
                        assign_employee_role,
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


@router.post("employee/role")
def assign_role_to_employee(data:EmployeeRole,db:Session=Depends(get_db)):
    data=assign_employee_role(db,data)
    if data:
        return {"message":"Role Updated Successfully to  Employee"}
    

