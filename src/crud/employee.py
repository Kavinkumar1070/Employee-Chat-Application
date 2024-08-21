from sqlalchemy.orm import Session
from src.models.employee import EmployeeEmploymentDetails
from src.models.personal import EmployeeOnboarding
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.schemas.employee import EmployeeEmploymentDetailsBase,EmployeeEmploymentDetailsUpdate


def create_employee_employment_details(db: Session, employee_employment_data:EmployeeEmploymentDetailsBase ):
    try:
        employee_onboarding = db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == employee_employment_data.employment_id).first()
        if not employee_onboarding:
            raise ValueError(f"No EmployeeOnboarding record found for id {employee_employment_data.get('id')}")

        employment_id = f"CDS{str(employee_employment_data.employment_id).zfill(4)}"
        print(employment_id)
        new_employment_details = EmployeeEmploymentDetails(
            employment_id=employment_id,  
            job_position=employee_employment_data.job_position,
            department=employee_employment_data.department,
            start_date=employee_employment_data.start_date,
            employment_type=employee_employment_data.employment_type,
            reporting_manager=employee_employment_data.reporting_manager,
            work_location=employee_employment_data.work_location,
            basic_salary=employee_employment_data.basic_salary,
            is_active=True,
            employee_id=employee_employment_data.employment_id
        )
        db.add(new_employment_details)
        db.commit()
        db.refresh(new_employment_details)
        return new_employment_details

    except SQLAlchemyError as e:
        db.rollback()
        raise
    except ValueError as e:
        raise


def get_employee_employment_details(db: Session, employee_id: int):
    return db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employment_id == employee_id).first()

def get_all_employee_employment_details(db: Session, employee_id: int):
    emp= db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employment_id == employee_id).first()
    return emp

def update_employee_employment_details(db: Session, updates: EmployeeEmploymentDetailsUpdate):
    employee_employment = db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employment_id == updates.employment_id).first()
    if not employee_employment:
        return None
    
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(employee_employment, key, value)
    

    db.commit()
    db.refresh(employee_employment)
    return employee_employment


def delete_employee_employment_details(db: Session, employee_id: int):
    employee_employment = db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.id == employee_id).first()
    if employee_employment:
        employee_employment.is_active=False
        db.commit()
    return employee_employment
