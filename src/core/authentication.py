from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from src.core.database import get_db
from src.core.utils import verify_password
from src.schemas.authentication import TokenData
from src.models.personal import EmployeeOnboarding
from src.models.role import Role
from src.models.association import employee_role
from src.models.employee import EmployeeEmploymentDetails

# Load environment variables from .env file
load_dotenv()

router = APIRouter()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router=APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_employee(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authentication": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: int = payload.get("sub")
        if employee_id is None:
            raise credentials_exception
        token_data = TokenData(employee_id=employee_id)
    except JWTError:
        raise credentials_exception
    
    employee = db.query(EmployeeOnboarding).filter(EmployeeOnboarding.id == token_data.employee_id).first()
    if employee is None:
        raise credentials_exception
    return employee


def authenticate_employee(db: Session, employee_email: str, password: str):
    employee = db.query(EmployeeEmploymentDetails).filter(EmployeeEmploymentDetails.employee_email == employee_email).first()
    if not employee:
        return None
    if not verify_password(password, employee.password):
        return None
    return employee


def get_current_user_roles(
    current_user: EmployeeOnboarding = Depends(get_current_employee),
    db: Session = Depends(get_db)
) -> list:
    roles = db.query(Role).join(employee_role).filter(employee_role.c.employee_id == current_user.id).all()
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have any assigned roles"
        )
    return [role.name for role in roles]

def get_current_employee_roles(
    current_user: int,
    db: Session = Depends(get_db)
) -> list:
    roles = db.query(Role).join(employee_role).filter(employee_role.c.employee_id == current_user).all()
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have any assigned roles"
        )
    return [role.name for role in roles]


def roles_required(*required_roles: str):
    def role_dependency(
        user_roles: list = Depends(get_current_user_roles)
    ):
        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for the current user's roles"
            )
    return role_dependency



@router.post("/token")
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    employee = authenticate_employee(db, form_data.username, form_data.password)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(employee.id)}, expires_delta=access_token_expires
    )
    role=get_current_employee_roles(employee.id,db,)
    return {"access_token": access_token, "token_type": "bearer","role":role}



@router.get("/admin-endpoint", dependencies=[Depends(roles_required("admin"))])
def read_employee_me(current_employee: EmployeeOnboarding = Depends(get_current_employee)):
    return current_employee


