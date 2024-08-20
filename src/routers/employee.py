from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.crud.employee import(
    create_employee_employment_details,
    get_employee_employment_details,
    update_employee_employment_details,
    delete_employee_employment_details,
    get_all_employee_employment_details
)
from src.schemas.employee import(
    EmployeeEmploymentDetailsCreate,
    EmployeeEmploymentDetailsUpdate,
    EmployeeEmploymentDetails
)

router = APIRouter(
    prefix="/employee",
    tags=["employee"],
    responses={400: {"message": "Not found"}}
)

@router.post("/employees/")
def create_employee(employee_employment: EmployeeEmploymentDetailsCreate, db: Session = Depends(get_db)):
    db_employee = create_employee_employment_details(db,employee_employment)
    return db_employee

@router.get("/employees/{employee_id}")
def read_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = get_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.get("/all-employees/{employee_id}")
def read_all_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = get_all_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"Full_Details":db_employee,"Personal_deatils":db_employee.employee}

@router.put("/employees/{employee_id}")
def update_employee( employee_update: EmployeeEmploymentDetailsUpdate, db: Session = Depends(get_db)):
    db_employee = update_employee_employment_details(db,employee_update)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = delete_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message":"The Employee is Deleted Successfully"}
