from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.crud.personal import create_employee, get_employees, get_employee, update_employee, delete_employee
from src.schemas.personal import EmployeeCreate,EmployeeUpdate
from typing import List, Optional
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

@router.post("/employees/")
def create_employee_route(employee: EmployeeCreate, db: Session = Depends(get_db)):
    # employee.DateOfBirth = convert_date_format(employee.DateOfBirth)
    return create_employee(db, employee)

@router.get("/employees/")
def read_employees_route(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_employees(db, skip=skip, limit=limit)

@router.get("/employees/{employee_id}")
def read_employee_route(employee_id: int, db: Session = Depends(get_db)):
    db_employee = get_employee(db, employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee


@router.put("/employees/{employee_id}")
async def update_employee_data(employee_id: int,employee_update: EmployeeUpdate,db: Session = Depends(get_db)):
    updated_employee = update_employee(db, employee_id, employee_update)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee

@router.delete("/employees/{employee_id}")
def delete_employee_route(employee_id: int, db: Session = Depends(get_db)):
    db_employee = delete_employee(db, employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee
