from src.core.database import get_db
from src.core.database import engine
from fastapi import FastAPI
from src import models
from src.routers import personal,employee

app=FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(personal.router)
app.include_router(employee.router)


@app.get("/")
def index():
    return "hi there"