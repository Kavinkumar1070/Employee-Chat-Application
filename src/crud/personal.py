from sqlalchemy.orm import Session
from src.models.personal import EmployeeOnboarding
from src.schemas.personal import EmployeeCreate,EmployeeUpdate

def create_employee(db: Session, employee: EmployeeCreate):
    db_employee = EmployeeOnboarding(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def get_employee(db: Session, employee_id: int):
    return db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_id).first()


def update_employee(db: Session, employee_id: int, update_data: EmployeeUpdate):
    db_employee = db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_id).first()
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
