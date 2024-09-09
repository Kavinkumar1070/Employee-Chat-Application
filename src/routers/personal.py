from fastapi import APIRouter, Depends, HTTPException,Path
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.personal import EmployeeOnboarding
from src.core.authentication import get_current_employee, get_current_employee_roles
from src.crud.personal import (
    create_employee,
    get_employee,
    update_employee,
    delete_employee,
    get_employee_admin,
    get_employee_teamlead,
    update_employee_teamlead,
)
from src.schemas.personal import EmployeeCreate, EmployeeUpdate, UpdateEmployeeAdmin
from src.core.utils import normalize_string, send_email
from src.core.authentication import roles_required
from datetime import datetime

router = APIRouter(
    prefix="/personal", tags=["Personal"], responses={400: {"message": "Not found"}}
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def convert_date_format(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Incorrect date format. Use MM/DD/YYYY."
        )


@router.post("/employees")
async def create_employee_route(
    employee: EmployeeCreate, db: Session = Depends(get_db)
):
    # Normalize strings
    employee.firstname = normalize_string(employee.firstname)
    employee.lastname = normalize_string(employee.lastname)
    employee.address = normalize_string(employee.address)
    employee.nationality = normalize_string(employee.nationality)
    employee.gender = normalize_string(employee.gender)
    employee.maritalstatus = normalize_string(employee.maritalstatus)
    employee.emailaddress = normalize_string(employee.emailaddress)

    # Create employee and get details
    details = create_employee(db, employee)  # Ensure create_employee is synchronous

    # Send the email asynchronously
    await send_email(
        recipient_email=details["emailaddress"],
        name=details["firstname"],
        lname=details["lastname"],
        Email=details["employee_email"],
        Password=details["password"],
    )

    return {"detail": "Email Send Successfully"}


@router.get(
    "/employees/{employee_id}",
    dependencies=[Depends(roles_required("employee", "teamlead", "admin"))],
)
async def read_employee_route(
    employee_id: str = Path(...),db: Session = Depends(get_db), current_employee=Depends(get_current_employee)
):
    current_employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    if employee_id=="me":
        employee_id=current_employee_id
    if employee_role.name == "employee":
        db_employee = get_employee(db, employee_id)
        return db_employee
    if employee_role.name == "admin":
        db_employee = get_employee_admin(db)
        return db_employee
    if employee_role.name == "teamlead":
        if  employee_id==current_employee.employment_id:
            db_employee = get_employee(db, employee_id)
        else:
            db_employee = get_employee_teamlead(db, employee_id,current_employee_id)
        return db_employee
    else:
        raise HTTPException(status_code=404, detail="Employee not found")

@router.put(
    "/employees/",
    dependencies=[Depends(roles_required("employee", "teamlead", "admin"))],
)
async def update_employee_data(
    employee_update: EmployeeUpdate,
    emp_data: UpdateEmployeeAdmin,
    db: Session = Depends(get_db),
    current_employee=Depends(get_current_employee),
):
    employee_id = current_employee.employment_id
    employee_role = get_current_employee_roles(current_employee.id, db)
    if employee_role.name == "employee":
        updated_employee = update_employee(db, employee_id, employee_update)
    if employee_role.name == "admin":
        updated_employee = update_employee(db, emp_data.employee_id, employee_update)
    if employee_role.name == "teamlead":
        updated_employee = update_employee_teamlead(
            db, emp_data.employee_id, employee_id, employee_update
        )
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee


@router.delete(
    "/employees/{employee_id}", dependencies=[Depends(roles_required("admin"))]
)
async def delete_employee_route(employee_id: str, db: Session = Depends(get_db)):
    db_employee = delete_employee(db, employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"details": "employee deleted successfully"}
