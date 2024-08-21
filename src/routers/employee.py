from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.core.utils import normalize_string
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
    employee_employment.job_position = normalize_string(employee_employment.job_position)
    employee_employment.department = normalize_string(employee_employment.department)
    employee_employment.start_date = employee_employment.start_date
    employee_employment.employment_type = normalize_string(employee_employment.employment_type)
    employee_employment.reporting_manager = normalize_string(employee_employment.reporting_manager) 
    employee_employment.work_location = normalize_string(employee_employment.work_location) 
    employee_employment.basic_salary = employee_employment.basic_salary
    return create_employee_employment_details(db,employee_employment)
    


@router.get("/all-employees/{employee_id}")
def read_all_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = get_all_employee_employment_details(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee_details = {
        "employment_id": db_employee.employment_id,
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
        "employee_data" :{
            "id": db_employee.employee.id,
            "firstname": db_employee.employee.firstname,  
            "lastname": db_employee.employee.lastname,  
            "dateofbirth": str(db_employee.employee.dateofbirth),  
            "contactnumber": db_employee.employee.contactnumber,  
            "emailaddress": db_employee.employee.emailaddress,  
            "address": db_employee.employee.address,  
            "nationality": db_employee.employee.nationality,  
            "gender": db_employee.employee.gender,  
            "maritalstatus": db_employee.employee.maritalstatus 
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
