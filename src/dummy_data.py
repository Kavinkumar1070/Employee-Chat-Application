from datetime import datetime, date
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker 
from models import Base, EmployeeOnboarding, EmployeeEmploymentDetails, Role, RoleFunction, employee_role
from src.models.leave import EmployeeLeave,LeaveDuration,LeaveStatus
from src.core.utils import hash_password
from fastapi import FastAPI
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")



# Create a new engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Create metadata
metadata = MetaData()

def insert_dummy_data():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Insert roles
    admin_role = Role(name="admin")
    teamleader_role = Role(name="teamleader")
    employee_role = Role(name="employee")
    
    session.add_all([admin_role, teamleader_role, employee_role])
    session.commit()

    # Insert role functions
    admin_functions = [
        RoleFunction(role_id=admin_role.id, function="edit employee", jsonfile="admin_edit_employee.json"),
        RoleFunction(role_id=admin_role.id, function="approve leave", jsonfile="admin_approve_leave.json"),
        RoleFunction(role_id=admin_role.id, function="share information", jsonfile="admin_share_info.json")
    ]

    teamleader_functions = [
        RoleFunction(role_id=teamleader_role.id, function="approve leave", jsonfile="teamleader_approve_leave.json"),
        RoleFunction(role_id=teamleader_role.id, function="apply leave", jsonfile="teamleader_apply_leave.json"),
        RoleFunction(role_id=teamleader_role.id, function="edit details", jsonfile="teamleader_edit_details.json")
    ]

    employee_functions = [
        RoleFunction(role_id=employee_role.id, function="apply leave", jsonfile="employee_apply_leave.json"),
        RoleFunction(role_id=employee_role.id, function="view leave by month", jsonfile="employee_view_leave.json"),
        RoleFunction(role_id=employee_role.id, function="delete leave", jsonfile="employee_delete_leave.json"),
        RoleFunction(role_id=employee_role.id, function="update personal details", jsonfile="employee_update_details.json")
    ]

    session.add_all(admin_functions + teamleader_functions + employee_functions)
    session.commit()

    # Insert employees
    admin_employee = EmployeeOnboarding(
        employment_id="cds0001",
        firstname="admin",
        lastname="admin",
        dateofbirth=date(1985, 7, 10),
        contactnumber=1112233445,
        emailaddress="hariprathap670@gmail.com",
        address="123 Admin St",
        nationality="American",
        gender="male",
        maritalstatus="Single"
    )

    teamleader_employee = EmployeeOnboarding(
        employment_id="cds0002",
        firstname="teamlead",
        lastname="tl",
        dateofbirth=date(1988, 3, 22),
        contactnumber=5556677889,
        emailaddress="kavin@gmail.com",
        address="456 Leader Rd",
        nationality="American",
        gender="Male",
        maritalstatus="Married"
    )

    regular_employee = EmployeeOnboarding(
        employment_id="cds0003",
        firstname="employee",
        lastname="emp",
        dateofbirth=date(1992, 11, 5),
        contactnumber=9998887770,
        emailaddress="employee@gmail.com",
        address="789 Worker Ave",
        nationality="American",
        gender="Non-Binary",
        maritalstatus="Single"
    )
    
    session.add_all([admin_employee, teamleader_employee, regular_employee])
    session.commit()

    # Insert employment details
    admin_password = hash_password("adminpass123")
    teamleader_password = hash_password("teamleadpass456")
    employee_password = hash_password("empass789")

    admin_employment_details = EmployeeEmploymentDetails(
        employee_email="admin@conversedatasolution.com",
        password=admin_password,
        job_position="Administrator",
        department="Administration",
        start_date=date(2020, 1, 1),
        employment_type="Full-time",
        reporting_manager=None,
        work_location="Main Office",
        basic_salary=80000.00,
        employee_id=admin_employee.employment_id  # Must match admin_employee.employment_id
    )

    teamleader_employment_details = EmployeeEmploymentDetails(
        employee_email="teamleader@conversedatasolution.com",
        password=teamleader_password,
        job_position="Team Leader",
        department="Engineering",
        start_date=date(2021, 6, 1),
        employment_type="Full-time",
        reporting_manager="cds0001",
        work_location="Main Office",
        basic_salary=75000.00,
        employee_id=teamleader_employee.employment_id  # Must match teamleader_employee.employment_id
    )

    regular_employment_details = EmployeeEmploymentDetails(
        employee_email="employee@conversedatasolution.com",
        password=employee_password,
        job_position="Software Engineer",
        department="Engineering",
        start_date=date(2022, 3, 15),
        employment_type="Full-time",
        reporting_manager="cds0002",
        work_location="Main Office",
        basic_salary=70000.00,
        employee_id=regular_employee.employment_id # Must match regular_employee.employment_id
    )

    session.add_all([admin_employment_details, teamleader_employment_details, regular_employment_details])
    session.commit()

    # Insert roles
    employee_role_table = Table('employee_role', metadata, autoload_with=engine)
    
    session.execute(employee_role_table.insert().values([
        {"employee_id": admin_employee.id, "role_id": admin_role.id},
        {"employee_id": teamleader_employee.id, "role_id": teamleader_role.id},
        {"employee_id": regular_employee.id, "role_id": employee_role.id}
    ]))
    session.commit()

    # Insert leaves
    leaves = [
        EmployeeLeave(
            employee_id=admin_employee.id,
            leave_type="Sick Leave",
            duration=LeaveDuration.ONE_DAY,
            start_date=date(2024, 9, 10),
            end_date=date(2024, 9, 10),
            status=LeaveStatus.APPROVED,
            reason="Flu",
            reject_reason=None
        ),
        EmployeeLeave(
            employee_id=teamleader_employee.id,
            leave_type="Vacation",
            duration=LeaveDuration.HALF_DAY,
            start_date=date(2024, 9, 15),
            end_date=date(2024, 9, 15),
            status=LeaveStatus.PENDING,
            reason="Family Event",
            reject_reason=None
        ),
        EmployeeLeave(
            employee_id=regular_employee.id,
            leave_type="Personal",
            duration=LeaveDuration.ONE_DAY,
            start_date=date(2024, 9, 20),
            end_date=date(2024, 9, 20),
            status=LeaveStatus.REJECTED,
            reason="Urgent Personal Matter",
            reject_reason="Insufficient Leave Balance"
        )
    ]

    session.add_all(leaves)
    session.commit()

if __name__ == "__main__":
    insert_dummy_data()
    print("Dummy data inserted successfully.")
