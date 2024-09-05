from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy.sql import func
from src.core.utils import send_email_leave
from src.models.leave import EmployeeLeave
from src.models.employee import EmployeeEmploymentDetails
from src.schemas.leave import EmployeeLeaveCreate, EmployeeLeaveUpdate, LeaveStatus

def create_employee_leave(db: Session, leave: EmployeeLeaveCreate,employee_id):
    leave_entries = []
    employee_data=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id==employee_id).first()
    if not employee_data :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee Not found")
    for i in range(leave.total_days):
        end_date = leave.start_date + timedelta(days=i)
        db_leave = EmployeeLeave(
            employee_id=employee_data.id,
            leave_type=leave.leave_type,
            duration=leave.duration,
            start_date=leave.start_date + timedelta(days=i),
            end_date=end_date,
            reason=leave.reason
        )
        leave_entries.append(db_leave)
        db.add(db_leave)
    db.commit()
    send_email_leave(employee_data.employee_email,employee_data.employee.firstname,employee_data.employee.lastname,db_leave.id,db_leave.reason,db_leave.status)
    return {"details":"leave applied successfully,Email send successfully"}

def get_employee_leave_by_month(db: Session, employee_id: str, month: int, year: int):
    employee_data=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id==employee_id).first()
    if not employee_data :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee Not found")
    return db.query(EmployeeLeave).filter(
        EmployeeLeave.employee_id == employee_data.id,
        func.extract('month', EmployeeLeave.start_date) == month,
        func.extract('year', EmployeeLeave.start_date) == year
    ).all()

def get_leave_by_employee_id(db: Session, employee_id: str):
    employee_data=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id==employee_id).first()
    if not employee_data :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee Not found")
    return db.query(EmployeeLeave).filter(
        EmployeeLeave.employee_id == employee_data.id
    ).all()


def get_leave_by_id(db: Session):
    return db.query(EmployeeLeave).filter(EmployeeLeave.status == "pending").all()



def update_employee_leave(db: Session, leave_update: EmployeeLeaveUpdate):
    employee_data=db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_id==leave_update.employee_id).first()
    if not employee_data :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee Not found") 
    db_leave = db.query(EmployeeLeave).filter(
        EmployeeLeave.id == leave_update.leave_id,
        EmployeeLeave.employee_id == employee_data.id
    ).first()
    if db_leave:
        if leave_update.status:
            db_leave.status = leave_update.status
        if leave_update.reason and leave_update.status == LeaveStatus.REJECTED:
            db_leave.reason = leave_update.reason
        db.commit()
        db.refresh(db_leave)

    return db_leave

# Delete a leave
def delete_employee_leave(db: Session, leave_id: int):
    db_leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if db_leave:
        db.delete(db_leave)
        db.commit()
    return db_leave
