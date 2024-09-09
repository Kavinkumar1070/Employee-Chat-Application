from fastapi import APIRouter, HTTPException, Depends, Query,Path
from sqlalchemy.orm import Session
from typing import Optional
from src.core.utils import normalize_string
from src.core.database import get_db
from src.core.authentication import (
    roles_required,
    get_current_employee,
    get_current_employee_roles,
)
from src.crud.employee import (
    create_employee_employment_details,
    update_employee_employment_details,
    delete_employee_employment_details,
    get_all_employee_employment_details,
    get_all_employee_teamlead,
)
from src.schemas.employee import (
    EmployeeEmploymentDetailsCreate,
    EmployeeEmploymentDetailsUpdate,
)

router = APIRouter(
    prefix="/employee", tags=["employee"], responses={400: {"message": "Not found"}}
)


@router.post("/employees/", dependencies=[Depends(roles_required("admin"))])
async def create_employee(
    employee_employment: EmployeeEmploymentDetailsCreate, db: Session = Depends(get_db)
):
    employee_employment.job_position = normalize_string(
        employee_employment.job_position
    )
    employee_employment.department = normalize_string(employee_employment.department)
    employee_employment.start_date = employee_employment.start_date
    employee_employment.employment_type = normalize_string(
        employee_employment.employment_type
    )
    employee_employment.work_location = normalize_string(
        employee_employment.work_location
    )
    employee_employment.basic_salary = employee_employment.basic_salary
    return create_employee_employment_details(db, employee_employment)


@router.get(
    "/employees/{employee_id}",
    dependencies=[Depends(roles_required("employee", "teamlead", "admin"))],
)
async def read_employee(
    employee_id: str = Path(...),  # Path parameter is required, but use a placeholder
    db: Session = Depends(get_db),
    current_employee=Depends(get_current_employee),
):
    current_employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)

    # Handle the case where 'me' is passed as the employee_id
    if employee_id == "me":
        employee_id = current_employee_id

    if employee_role.name == "employee":
        db_employee = get_all_employee_employment_details(db, current_employee_id)
    elif employee_role.name == "admin":
        db_employee = get_all_employee_employment_details(db, employee_id)
    elif employee_role.name == "teamlead":
        if  employee_id==current_employee.employment_id:
            db_employee = get_all_employee_employment_details(db, employee_id)
        else:
            db_employee = get_all_employee_teamlead(db, employee_id, reporting_manager=current_employee_id)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Prepare the response with employee details
    employee_details = {
        "employee_email": db_employee.employee_email,
        "job_position": db_employee.job_position,
        "department": db_employee.department,
        "start_date": db_employee.start_date,
        "employment_type": db_employee.employment_type,
        "reporting_manager": db_employee.reporting_manager,
        "work_location": db_employee.work_location,
        "basic_salary": db_employee.basic_salary,
        "is_active": db_employee.is_active,
        "releave_date": str(db_employee.releave_date),
        "employee_data":db_employee.employee.employment_id,
        "employee_name":db_employee.employee.firstname
    }

    return employee_details


@router.put("/employees/", dependencies=[Depends(roles_required("admin"))])
async def update_employee(
    employee_update: EmployeeEmploymentDetailsUpdate, db: Session = Depends(get_db)
):
    db_employee = update_employee_employment_details(db, employee_update)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee


@router.delete(
    "/employees/{employee_id}", dependencies=[Depends(roles_required("admin"))]
)
async def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = delete_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "The Employee is Deleted Successfully"}
