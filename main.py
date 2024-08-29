from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.core.database import get_db, engine
from src import models
from src.routers import personal, employee, role
from src.core.authentication import router as auth_router, authenticate_employee, create_access_token
from pathlib import Path
from fastapi.responses import HTMLResponse
from src.core.authentication import *
from src.core.authentication import oauth2_scheme,get_current_user_function


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


from fastapi.staticfiles import StaticFiles

app.mount("/templates", StaticFiles(directory=Path(__file__).resolve().parent / "templates"), name="templates")


app.include_router(personal.router)
app.include_router(employee.router)
app.include_router(role.router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
def get():
    file_path = Path(__file__).resolve().parent / "templates" / "index.html"
    if not file_path.exists():
        return HTMLResponse("File not found", status_code=404)
    return HTMLResponse(file_path.read_text())



    
@app.get("/profile")
async def get_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    db_user =  get_current_user_function(db, token)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authenticated"
        )
    return db_user