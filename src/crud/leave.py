from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy.sql import func
from src.core.utils import send_email_leave
from src.models.leave import EmployeeLeave
from src.models.employee import EmployeeEmploymentDetails
from src.schemas.leave import EmployeeLeaveCreate, EmployeeLeaveUpdate, LeaveStatus


def create_employee_leave(db: Session, leave: EmployeeLeaveCreate, employee_id: str):
    leave_entries = []
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee Not found"
        )
    for i in range(leave.total_days):
        end_date = leave.start_date + timedelta(days=i)
        db_leave = EmployeeLeave(
            employee_id=employee_data.id,
            leave_type=leave.leave_type,
            duration=leave.duration,
            start_date=leave.start_date + timedelta(days=i),
            end_date=end_date,
            reason=leave.reason,
        )
        leave_entries.append(db_leave)
        db.add(db_leave)
    db.commit()
    employee_code = employee_data.employee_id
    employee_email = employee_data.employee_email
    employee_firstname = employee_data.employee.firstname
    employee_lastname = employee_data.employee.lastname
    return {
        "leave": db_leave.id,
        "reason": db_leave.reason,
        "status": db_leave.status.value,
        "employee_email": employee_email,
        "employee_code": employee_code,
        "employee_firstname": employee_firstname,
        "employee_lastname": employee_lastname,
    }


def get_employee_leave_by_month(db: Session, employee_id: str, month: int, year: int):
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee Not found"
        )
    return (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.employee_id == employee_data.id,
            func.extract("month", EmployeeLeave.start_date) == month,
            func.extract("year", EmployeeLeave.start_date) == year,
        )
        .all()
    )


def get_leave_by_employee_id(db: Session, employee_id: str):
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == employee_id)
        .first()
    )
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee Not found"
        )
    return (
        db.query(EmployeeLeave)
        .filter(EmployeeLeave.employee_id == employee_data.id)
        .all()
    )


def get_leave_by_employee_Team(db: Session, employee_id: str, report_manager: str):
    # Query to get employee data based on employee_id and report_manager
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == employee_id,
            EmployeeEmploymentDetails.reporting_manager == report_manager,
        )
        .first()
    )

    if employee_data:
        # If employee data is found, return their leave records
        return (
            db.query(EmployeeLeave)
            .filter(EmployeeLeave.employee_id == employee_data.id)
            .all()
        )
    else:
        # If employee data is not found, get the reporting manager details
        report = (
            db.query(EmployeeEmploymentDetails)
            .filter(EmployeeEmploymentDetails.employee_id == report_manager)
            .first()
        )
        report_manager_data = (
            db.query(EmployeeLeave)
            .filter(EmployeeLeave.employee_id == report.id)
            .first()
        )

        if not report_manager_data:
            # If reporting manager data is also not found, raise a 404 error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee and Reporting Manager Not Found",
            )

        # Return the reporting manager details
        return report_manager_data


def get_leave_by_id(db: Session, current_employee_id: str):
    data_id = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.employee_id == current_employee_id)
        .first()
    )
    return (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.status == "pending", EmployeeLeave.employee_id == data_id.id
        )
        .all()
    )


def get_leave_by_admin(db: Session):
    return db.query(EmployeeLeave).filter(EmployeeLeave.status == "pending").all()


def get_leave_by_report_manager(db: Session, report_manager_id: str):
    # Query to get all employees reporting to the given manager
    employees = (
        db.query(EmployeeEmploymentDetails)
        .filter(EmployeeEmploymentDetails.reporting_manager == report_manager_id)
        .all()
    )

    # If no employees found, raise a 404 error
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employees found for this reporting manager",
        )

    # Extract the employee IDs from the employment details
    employee_ids = [employee.id for employee in employees]

    # Query to get all pending leave records for the employees
    leave_details = (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.employee_id.in_(employee_ids),
            EmployeeLeave.status == "pending",
        )
        .all()
    )

    # If no leave records found, raise a 404 error
    if not leave_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending leave records found for the employees",
        )

    return leave_details


def update_employee_leave(db: Session, leave_update: EmployeeLeaveUpdate):
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == leave_update.employee_id,
        )
        .first()
    )

    # If employee not found, raise an exception
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    # Query to find the leave request of the employee
    db_leave = (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.id == leave_update.leave_id,
            EmployeeLeave.employee_id == employee_data.id,
        )
        .first()
    )

    # If leave request found, update the details
    if db_leave:
        if leave_update.status:
            db_leave.status = leave_update.status
            db_leave.reason = "Leave Granted"
        if leave_update.reason and leave_update.status == LeaveStatus.REJECTED:
            db_leave.reason = leave_update.reason

        db.commit()  # Commit the changes
        db.refresh(db_leave)  # Refresh the instance

        # Set the employee email for sending a notification

        # Send an email notification asynchronously
    # Make sure to return a regular, synchronous object (not a coroutine)
    employee_code = employee_data.employee_id
    employee_email = employee_data.employee_email
    employee_firstname = employee_data.employee.firstname
    employee_lastname = employee_data.employee.lastname
    return {
        "leave": db_leave.id,
        "reason": db_leave.reason,
        "status": db_leave.status.value,
        "employee_email": employee_email,
        "employee_code": employee_code,
        "employee_firstname": employee_firstname,
        "employee_lastname": employee_lastname,
    }


def update_employee_teamlead(
    db: Session, report_manager: str, leave_update: EmployeeLeaveUpdate
):
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == leave_update.employee_id,
            EmployeeEmploymentDetails.reporting_manager == report_manager,
        )
        .first()
    )
    # If employee not found, raise an exception
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    db_leave = (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.id == leave_update.leave_id,
            EmployeeLeave.employee_id == employee_data.id,
        )
        .first()
    )

    # If leave request found, update the details
    if db_leave:
        if leave_update.status:
            db_leave.status = leave_update.status
            db_leave.reason = "Leave Granted"
        if leave_update.reason and leave_update.status == LeaveStatus.REJECTED:
            db_leave.reason = leave_update.reason

        db.commit()  # Commit the changes
        db.refresh(db_leave)  # Refresh the instance

        # Set the employee email for sending a notification

        # Send an email notification asynchronously
    # Make sure to return a regular, synchronous object (not a coroutine)
    employee_code = employee_data.employee_id
    employee_email = employee_data.employee_email
    employee_firstname = employee_data.employee.firstname
    employee_lastname = employee_data.employee.lastname
    return {
        "leave": db_leave.id,
        "reason": db_leave.reason,
        "status": db_leave.status.value,
        "employee_email": employee_email,
        "employee_code": employee_code,
        "employee_firstname": employee_firstname,
        "employee_lastname": employee_lastname,
    }


# Delete a leave
def delete_employee_leave(db: Session, employee_id: str, leave_id: int):
    db_leave = (
        db.query(EmployeeLeave)
        .filter(EmployeeLeave.employee_id == employee_id, EmployeeLeave.id == leave_id)
        .first()
    )
    if not db_leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No leave applied"
        )
    db.delete(db_leave)
    db.commit()
    return db_leave
