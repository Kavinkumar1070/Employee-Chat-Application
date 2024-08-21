from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.crud.employee import(
    create_employee_employment_details,
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



@router.get("/all-employees/{employee_id}")
def read_all_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = get_all_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee_details = {
        "id": db_employee.id,
        "department": db_employee.department,
        "employment_type": db_employee.employment_type,
        "work_location": db_employee.work_location,
        "is_active": db_employee.is_active,
        "employee_id": db_employee.employee_id,
        "employment_id": db_employee.employment_id,
        "job_position": db_employee.job_position,
        "start_date": str(db_employee.start_date),
        "reporting_manager": db_employee.reporting_manager,
        "basic_salary": db_employee.basic_salary,
        "releave_date": str(db_employee.releave_date),
        "employee": {
            "FirstName": db_employee.employee.FirstName,
            "DateOfBirth": str(db_employee.employee.DateOfBirth),
            "id": db_employee.employee.id,
            "EmailAddress": db_employee.employee.EmailAddress, 
            "Nationality": db_employee.employee.Nationality,
            "MaritalStatus": db_employee.employee.MaritalStatus,
            "LastName": db_employee.employee.LastName,
            "ContactNumber": db_employee.employee.ContactNumber,
            "Address": db_employee.employee.Address,
            "Gender": db_employee.employee.Gender
        }
    }
    
    return {"Full_Details": [employee_details]}

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
