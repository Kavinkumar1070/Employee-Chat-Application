from sqlalchemy.orm import Session
from fastapi import HTTPException,status
from src.models.personal import EmployeeOnboarding
from src.schemas.personal import EmployeeCreate,EmployeeUpdate

def create_employee(db: Session, employee: EmployeeCreate):
    exist_number=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.contactnumber==employee.contactnumber).first()
    exist_email=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.emailaddress==employee.emailaddress).first()
    if exist_number or exist_email :
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED,detail="contactnumber or emailaddress already exists")
    new_details = EmployeeOnboarding(  
            firstname=employee.firstname,
            lastname=employee.lastname,
            dateofbirth=employee.dateofbirth,
            contactnumber=employee.contactnumber,
            emailaddress=employee.emailaddress,
            address=employee.address,
            nationality=employee.nationality,
            gender=employee.gender,
            maritalstatus=employee.maritalstatus
        )
    db.add(new_details)
    db.commit()
    db.refresh(new_details)
    return new_details


def get_employee(db: Session, employee_id: int):
    return db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_id).first()


def update_employee(db: Session, employee_id: int, update_data: EmployeeUpdate):
    db_employee = db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_id).first()
    exist_number=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.contactnumber==update_data.contactnumber).first()
    exist_email=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.emailaddress==update_data.emailaddress).first()
    if exist_number or exist_email :
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED,detail="contactnumber or emailaddress already exists")
    if db_employee is None:
        return None

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_employee, key, value)
    
    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, employee_id: int):
    db_employee = db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_id).first()
    if db_employee:
        db.delete(db_employee)
        db.commit()
        return db_employee
    return None
