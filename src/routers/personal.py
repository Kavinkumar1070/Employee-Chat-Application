from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.crud.personal import create_employee, get_employee, update_employee, delete_employee
from src.schemas.personal import EmployeeCreate,EmployeeUpdate
from src.core.utils import normalize_string,send_email
from src.core.authentication import roles_required
from datetime import datetime

router = APIRouter(
    prefix="/personal",
    tags=["Personal"],
    responses={400: {"message": "Not found"}}
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def convert_date_format(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Incorrect date format. Use MM/DD/YYYY.")

@router.post("/employees")
async def create_employee_route(employee: EmployeeCreate, db: Session = Depends(get_db)):
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
        recipient_email=details['emailaddress'],
        name=details['firstname'],
        lname=details['lastname'],
        Email=details['employee_email'],
        Password=details['password']
    )
    
    
    return {"detail":"Email Send Successfully"}


@router.get("/employees/{employee_id}", dependencies=[Depends(roles_required("admin"))])
async def read_employee_route(employee_id: str, db: Session = Depends(get_db)):
    db_employee = get_employee(db, employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee


@router.put("/employees/{employee_id}", dependencies=[Depends(roles_required("admin"))])
async def update_employee_data(employee_id: str,employee_update: EmployeeUpdate,db: Session = Depends(get_db)):
    updated_employee = update_employee(db, employee_id, employee_update)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee


@router.delete("/employees/{employee_id}", dependencies=[Depends(roles_required("admin"))])
async def delete_employee_route(employee_id: str, db: Session = Depends(get_db)):
    db_employee = delete_employee(db, employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee
