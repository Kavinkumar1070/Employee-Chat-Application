from sqlalchemy.orm import Session
from src.models.employee import EmployeeEmploymentDetails
from src.models.personal import EmployeeOnboarding
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.core.utils import normalize_string
from src.schemas.employee import (
    EmployeeEmploymentDetailsBase,
    EmployeeEmploymentDetailsUpdate,
    Login,
)
from src.models.association import employee_role


def create_employee_employment_details(
    db: Session, employee_employment_data: EmployeeEmploymentDetailsBase
):
    try:
        employee_onboarding = (
            db.query(EmployeeOnboarding)
            .filter(
                EmployeeOnboarding.employment_id
                == employee_employment_data.employment_id
            )
            .first()
        )
        if not employee_onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No EmployeeOnboarding record found for id {employee_employment_data.employment_id}",
            )
        reporting_manager = (
            db.query(EmployeeOnboarding)
            .filter(
                EmployeeOnboarding.employment_id
                == employee_employment_data.reporting_manager
            )
            .first()
        )
        if not employee_onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No EmployeeOnboarding record found for id {employee_employment_data.reporting_manager}",
            )
        if not reporting_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting_manager id should not be Empty or Not found",
            )
        inter_data = (
            db.query(employee_role)
            .filter(employee_role.c.employee_id == reporting_manager.id)
            .first()
        )
        if not inter_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting_manager is Not  Association With the  role",
            )

        new_employment_details = EmployeeEmploymentDetails(
            job_position=employee_employment_data.job_position,
            department=employee_employment_data.department,
            start_date=employee_employment_data.start_date,
            employment_type=employee_employment_data.employment_type,
            reporting_manager=employee_employment_data.reporting_manager,
            work_location=employee_employment_data.work_location,
            basic_salary=employee_employment_data.basic_salary,
            is_active=True,
            employee_id=employee_employment_data.employment_id,
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


def get_all_employee_employment_details(db: Session, employee_id: str):
    emp = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    return emp


def get_all_employee_teamlead(db: Session, employee_id: str, reporting_manager: str):
    emp = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == employee_id,
            EmployeeEmploymentDetails.reporting_manager == reporting_manager,
        )
        .first()
    )
    return emp


def update_employee_employment_details(
    db: Session, updates: EmployeeEmploymentDetailsUpdate
):

    employee_employment = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == updates.employment_id)
        .first()
    )

    if not employee_employment:
        return None
    reporting_manager = (
        db.query(EmployeeOnboarding)
        .filter(EmployeeOnboarding.employment_id == updates.reporting_manager)
        .first()
    )
    if not reporting_manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting_manager id should not be Empty or Not found",
        )
    inter_data = (
        db.query(employee_role)
        .filter(employee_role.c.employee_id == reporting_manager.id)
        .first()
    )

    if not inter_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting manager is not associated with a role",
        )

    for key, value in updates.dict(exclude_unset=True).items():
        if key in ["job_position", "department", "work_location", "employee_email"]:
            setattr(employee_employment, key, normalize_string(value))
        elif key == "basic_salary" and value is not None:
            setattr(employee_employment, key, float(value))
        elif key == "start_date" and isinstance(value, date):
            setattr(employee_employment, key, value)
        else:
            setattr(employee_employment, key, value)

    db.commit()
    db.refresh(employee_employment)
    return employee_employment


def delete_employee_employment_details(db: Session, employee_id: str):
    employee_employment = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    if employee_employment:
        employee_employment.is_active = False
        db.commit()
    return employee_employment
