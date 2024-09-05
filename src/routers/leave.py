from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.core.authentication import roles_required
from src.models.personal import EmployeeOnboarding
from src.core.authentication import get_current_employee
from src.schemas.leave import EmployeeLeaveCreate, EmployeeLeaveResponse, EmployeeLeaveUpdate
from src.crud.leave import create_employee_leave,update_employee_leave,delete_employee_leave,get_leave_by_employee_id,get_leave_by_id,get_employee_leave_by_month

router = APIRouter(
    prefix="/leave",
    tags=["leave"],
    responses={400: {"message": "Not found"}}
)


@router.post("/", dependencies=[Depends(roles_required("employee","admin","teamleader"))])
def apply_leave(
    leave: EmployeeLeaveCreate, 
    db: Session = Depends(get_db),
    current_employee: EmployeeOnboarding = Depends(get_current_employee)  # Ensure this is the correct type
):
    # Accessing employee_id directly from the object
    employee_id = current_employee.employment_id
    if not employee_id:
        raise HTTPException(status_code=400, detail="Invalid employee data")

    return create_employee_leave(db, leave, employee_id)


@router.get("/{employee_id}",dependencies=[Depends(roles_required("teamleader","admin"))])
def get_leaves_by_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee=get_leave_by_employee_id(db, employee_id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not applied for leave")
    return db_employee


@router.get("/pending/teamleader",dependencies=[Depends(roles_required("teamleader","admin"))])
def get_leave_by(db: Session = Depends(get_db)):
    db_leave = get_leave_by_id(db)
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave_details = [
        {"employee_id": leave.employee.employee_id, "leave_id": leave.id} for leave in db_leave
    ]

    return leave_details

@router.get("/month/{month}/{year}",dependencies=[Depends(roles_required("employee","admin","teamleader"))])
def get_leave_by_month(month: int, year: int, db: Session = Depends(get_db),current_employee: EmployeeOnboarding = Depends(get_current_employee)):
    employee_id = current_employee.employment_id
    return get_employee_leave_by_month(db, employee_id, month, year)



@router.put("/update",dependencies=[Depends(roles_required("teamleader","admin"))])
def update_leave( leave: EmployeeLeaveUpdate, db: Session = Depends(get_db)
):
    
    if leave.status == "approved":
        db_leave = update_employee_leave(db, leave)
    elif leave.status == "rejected":
        if not  leave.reason or not leave.reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Please provide a reason for rejecting the leave."
            )
        db_leave = update_employee_leave(db,leave)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid leave status provided."
        )
    
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    return db_leave

@router.delete("/{leave_id}",dependencies=[Depends(roles_required("employee","admin","teamleader"))])
def delete_leave(leave_id: int, db: Session = Depends(get_db),current_user=Depends(get_current_employee)):
    success = delete_employee_leave(db,current_user.id ,leave_id)
    if not success:
        raise HTTPException(status_code=404, detail="Leave not found")
    return {"leave deleted successfully"}