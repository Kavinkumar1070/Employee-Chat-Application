from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy.sql import func
from src.core.utils import send_email_leave,normalize_string
from src.models.leave import EmployeeLeave,LeaveDuration,LeaveStatus,LeaveCalendar
from src.models.employee import EmployeeEmploymentDetails
from src.models.association import employee_role
from src.models.role import Role
from sqlalchemy.exc import IntegrityError
from src.schemas.leave import EmployeeLeaveCreate, EmployeeLeaveUpdate,LeaveCalendarUpdate

def adjust_leave_balance(db: Session, employee_id: int, employee_employment_id: str, leave_type: str):
    # Define mappings for leave types
    leave_fields = {
        "sick": ("sick_leave", "Sick leave quota is exhausted. You cannot approve the additional sick leave."),
        "personal": ("personal_leave", "Personal leave quota is exhausted. You cannot approve the additional personal leave."),
        "vacation": ("vacation_leave", "Vacation leave quota is exhausted. You cannot approve the additional vacation leave."),
        "unpaid": ("unpaid_leave", "Unpaid leave quota is exhausted. You cannot approve the additional unpaid leave.")
    }
    
    # Retrieve the leave calendar entry for the given employee_id
    print(employee_employment_id)
    print(employee_id)
    print(leave_type)
    leave_calendar = db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == employee_id).first()
    
    if not leave_calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LeaveCalendar entry not found for the specified employee."
        )
    
    if leave_type not in leave_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leave type specified. Please use 'sick', 'personal', 'vacation', or 'unpaid'."
        )
    
    # Get the field name and error message from the mappings
    field_name, error_message = leave_fields[leave_type]
    
    # Get the current leave balance for the specified leave type
    current_balance = getattr(leave_calendar, field_name)
    
    # Check the leave type to apply the correct logic
    if leave_type == "unpaid":
        # Increase unpaid leave balance by 1
        setattr(leave_calendar, field_name, current_balance + 1)
    else:
        # For other leave types, check and decrement if applicable
        if current_balance > 0:
            setattr(leave_calendar, field_name, current_balance - 1)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No available {leave_type} leave. You cannot 'apply' (or) 'approve' the {leave_type} leave for this employee_id '{employee_employment_id}'"
            )
    
    try:
        db.commit()  # Commit the changes to the database
        db.refresh(leave_calendar)  # Refresh the instance to reflect updated data
    except Exception as e:
        db.rollback()  # Roll back the transaction in case of an error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the leave balance."
        )
    
    return leave_calendar

def create_leave_balance(db: Session, employee_id: int,employee_employment_id:str, leave_type: str):
    # Define mappings for leave types
    leave_fields = {
        "sick": ("sick_leave", "Sick leave quota is exhausted. You cannot approve the additional sick leave."),
        "personal": ("personal_leave", "Personal leave quota is exhausted. You cannot approve the additional personal leave."),
        "vacation": ("vacation_leave", "Vacation leave quota is exhausted. You cannot approve the additional vacation leave."),
        "unpaid": ("unpaid_leave", "unpaid leave quota is exhausted. You cannot approve the additional vacation leave.")
    }
    
    # Retrieve the leave calendar entry for the given employee_id
    print(employee_employment_id)
    print(employee_id)
    leave_calendar = db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == employee_id).first()
    
    if not leave_calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LeaveCalendar entry not found for the specified employee."
        )
    
    if leave_type not in leave_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leave type specified. Please use 'sick', 'personal', or 'vacation'."
        )
    
    # Get the field name and error message from the mappings
    field_name, error_message = leave_fields[leave_type]
    
    # Get the current leave balance for the specified leave type
    current_balance = getattr(leave_calendar, field_name)
    
    if current_balance > 0:
        if field_name == "unpaid":
            pass
        setattr(leave_calendar, field_name, current_balance - 1)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No available {leave_type} leave. You cannot 'apply'  {leave_type} Leave Please Select Other Option"
        )
    
    try:
        db.commit()  # Commit the changes to the database
        db.refresh(leave_calendar)  # Refresh the instance to reflect updated data
    except Exception as e:
        db.rollback()  # Roll back the transaction in case of an error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the leave balance."
        )
    
    return leave_calendar



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
    def map_leave_duration(leave_duration_str: str):
        if leave_duration_str.lower() == 'oneday':
            return LeaveDuration.ONE_DAY
        elif leave_duration_str.lower() == 'halfday':
            return LeaveDuration.HALF_DAY
        else:
            raise ValueError("Invalid leave duration")
    leave.duration = map_leave_duration(leave.duration.value)
    leave_type=leave.leave_type
    create_leave_balance(db, employee_data.id,employee_data.employee_id,leave_type)
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
    other_leave=[leave.id for leave in leave_entries ]
    return {
        "leave": db_leave.id,
        "reason": db_leave.reason,
        "status": db_leave.status.value,
        "employee_email": employee_email,
        "employee_code": employee_code,
        "employee_firstname": employee_firstname,
        "employee_lastname": employee_lastname,
        "other_entires":other_leave
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
    data= (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.employee_id == employee_data.id,
            func.extract("month", EmployeeLeave.start_date) == month,
            func.extract("year", EmployeeLeave.start_date) == year,
        )
        .all()
    )
    return data
    
def get_employee_leave_by_month_tl(db: Session, employee_id: str  ,report_manager:str , month: int, year: int):
    data= (
            db.query(EmployeeEmploymentDetails)
            .filter(EmployeeEmploymentDetails.employee_id == employee_id,
                    EmployeeEmploymentDetails.reporting_manager == report_manager)
            .first()
        )
    if data:   
        return (
            db.query(EmployeeLeave)
            .filter(
                EmployeeLeave.employee_id == data.id,
                func.extract("month", EmployeeLeave.start_date) == month,
                func.extract("year", EmployeeLeave.start_date) == year,
            )
            .all()
            )
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee not found")

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


def get_leave_by_employee_team(db: Session, employee_id: str, report_manager: str):
    # Query to get employee data based on employee_id and report_manager
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.employee_id == employee_id,
            EmployeeEmploymentDetails.reporting_manager == report_manager,
        )
        .first()
    )
    if  employee_data:   # If employee data is found, return their leave records
        leave_records = (
                db.query(EmployeeLeave)
                .filter(EmployeeLeave.employee_id == employee_data.id)
                .all()
        )
        
        return leave_records
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Can Not Access Employee Details")




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
    manager=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id == report_manager_id).first()
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
    employee_ids.append(manager.id)
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
    # Query to find the leave request of the employee
    db_leave = (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.id == leave_update.leave_id
        )
        .first()
    )
    if not db_leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Leave not found")
    employee_id=db_leave.employee_id
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.id == employee_id,
        )
        .first()
    )
    # If employee not found, raise an exception
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    print(employee_data.employee_id)
    print("value",leave_update.status)
    # If leave request found, update the details
    if db_leave:
        if leave_update.status == LeaveStatus.APPROVED.value:
            db_leave.status = LeaveStatus.APPROVED
            if leave_update.reason:
                db_leave.reject_reason = leave_update.reason
            else:    
                db_leave.reject_reason = "Leave Granted"  
        if leave_update.reason and leave_update.status == LeaveStatus.REJECTED.value:
            db_leave.status = LeaveStatus.REJECTED
            db_leave.reject_reason = leave_update.reason
        leave_type=normalize_string(db_leave.leave_type)
        adjust_leave_balance(db, employee_id,employee_data.employee_id, leave_type)
        db.commit()  # Commit the changes
        db.refresh(db_leave)  # Refresh the instance
    if not db_leave or db_leave.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="leave not found"
        )
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
        "other_entires":" "
    }



def update_employee_teamlead(
    db: Session, report_manager: str, leave_update: EmployeeLeaveUpdate
):
    db_leave = (
        db.query(EmployeeLeave)
        .filter(
            EmployeeLeave.id == leave_update.leave_id
        )
        .first()
    )
    if not db_leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Leave not found")
    employee_id=db_leave.employee_id
    employee_data = (
        db.query(EmployeeEmploymentDetails)
        .filter(
            EmployeeEmploymentDetails.id == employee_id,
            EmployeeEmploymentDetails.reporting_manager == report_manager,
        )
        .first()
    )
    # If employee not found, raise an exception
    if not employee_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found or not authenticated to access the employee"
        )

    # If leave request found, update the details
    if db_leave:
        if leave_update.status == LeaveStatus.APPROVED.value:
            db_leave.status = LeaveStatus.APPROVED
            if leave_update.reason:
                db_leave.reject_reason = leave_update.reason
            else:    
                db_leave.reject_reason = "Leave Granted"
              
        if leave_update.reason and leave_update.status == LeaveStatus.REJECTED.value:
            db_leave.status = LeaveStatus.REJECTED
            db_leave.reject_reason = leave_update.reason
        leave_type=normalize_string(db_leave.leave_type)
        adjust_leave_balance(db, employee_id,employee_data.employee_id, leave_type)
        db.commit()  # Commit the changes
        db.refresh(db_leave)  # Refresh the instance
    if not db_leave or db_leave.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="leave not found"
        )
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
        "other_entires":" "
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



def leave_calender(db: Session):
    # Retrieve roles for the given employee_id and role_id
    roles = db.query(employee_role).all()

    for role in roles:
        # Get role data from the Role table
        role_data = db.query(Role).filter(Role.id == role.role_id).first()
        if not role_data:
            continue  # Skip if no role data is found
        # Check if an entry already exists in LeaveCalendar
        leave_calendar = db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == role.employee_id).first()
        
        if leave_calendar:
            # Update existing LeaveCalendar entry
            leave_calendar.sick_leave = role_data.sick_leave
            leave_calendar.personal_leave = role_data.personal_leave
            leave_calendar.vacation_leave = role_data.vacation_leave
        else:
            # Create a new LeaveCalendar entry
            leave_calendar = LeaveCalendar(
                employee_id=role.employee_id,
                sick_leave=role_data.sick_leave,
                personal_leave=role_data.personal_leave,
                vacation_leave=role_data.vacation_leave
            )
            db.add(leave_calendar)
            print(leave_calendar)

    try:
        db.commit()  
    except IntegrityError as e:
        db.rollback()  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving leave calendar data"
        )
    
    return {"message": "Leave calendar created successfully"}

def get_calender(db:Session, employee_id:int):
    data=db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == employee_id).first()
    return {
        "sick_leave":data.sick_leave,
        "personal_leave":data.personal_leave,
        "vacation_leave":data.vacation_leave,
    }

def get_calender_admin(db:Session, employee_id:str):
    employee_data=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id == employee_id).first()
    data=db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == employee_data.id).first()
    return {
        "sick_leave":data.sick_leave,
        "personal_leave":data.personal_leave,
        "vacation_leave":data.vacation_leave,
    }


def update_leave_calendar(db: Session, employee_id: int, leave_update: LeaveCalendarUpdate):
    leave_calendar = db.query(LeaveCalendar).filter(LeaveCalendar.employee_id == employee_id).first()
    if leave_calendar:
        for key, value in leave_update.dict(exclude_unset=True).items():
            setattr(leave_calendar, key, value)
        db.commit()
        db.refresh(leave_calendar)
        return leave_calendar
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LeaveCalendar entry not found")
