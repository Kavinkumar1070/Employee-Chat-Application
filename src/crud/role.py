from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from sqlalchemy import insert
                       
from src.models.role import Role
from src.schemas.role import EmployeeRole
from src.models.personal import EmployeeOnboarding
from src.models.association import employee_role


def create(db:Session,name:str):
    role_check=db.query(Role).filter(Role.name==name).first()
    if role_check:
        return False
    else:
        role=Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
     
def get_role(db: Session, role_name: str):
        role=db.query(Role).filter(Role.name == role_name).first()
        return role


def delete(db: Session, db_role:int ):
    role=db.query(Role).filter(Role.id == db_role).first()
    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}


def update(db: Session, role_id: int, new_name: str):
    role = db.query(Role).filter(Role.id == role_id).first()
    try:
        if role:
            role.name = new_name
            db.commit()
            db.refresh(role)
        return role
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="role name is already exists")


def get(db: Session, role_id: int):
    single_role=db.query(Role).filter(Role.id == role_id).first()
    return single_role


def assign_employee_role(db:Session,data:EmployeeRole):
    employee_details=db.query(EmployeeOnboarding).filter(EmployeeOnboarding.employment_id==data.employee_id).first()
    if not employee_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Employee not Found")
    role_details=db.query(Role).filter(Role.id==data.role_id).first()
    if not role_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Role not Found")
    
    db_employee_role = db.query(employee_role).filter(
        employee_role.c.employee_id == employee_details.id,
        employee_role.c.role_id == data.role_id
    ).first()
    if not db_employee_role:
        new_employee_role = {
            "employee_id": employee_details.id,
            "role_id": data.role_id
        }
        insert_statement = insert(employee_role).values(new_employee_role)
        db.execute(insert_statement)
        db.commit() 
    return new_employee_role


