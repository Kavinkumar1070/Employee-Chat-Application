from sqlalchemy import Column, Integer, String, ForeignKey, Table,UniqueConstraint
from src.core.database import Base


employee_role = Table(
    'employee_role', 
    Base.metadata,
    Column('employee_id', Integer, ForeignKey('employee_onboarding.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)
