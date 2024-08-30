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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import WebSocket, WebSocketDisconnect
import logging
import json
from function import *
from api_call import *


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            print("data_json",data_json)
            user_message = data_json.get("message")
            role = data_json.get("role")

            if user_message.lower() == 'quit':
                await websocket.send_text("Goodbye, Thanks for using our app!")
                break
            else:
                jsonfile = choose_json(role)
                print("jsonfile selected :",jsonfile)
                query, project_name = await get_project_details(websocket, user_message,jsonfile)
                print("query :",query)
                print("project_name :",project_name)
                project_details = get_project_script(project_name,jsonfile)
                payload_details = split_payload_fields(project_details)
                filled_cleaned = await fill_payload_values(websocket, query, payload_details,jsonfile)
                print("filled_cleaned :",filled_cleaned)
                validate_payload = validate(project_details, filled_cleaned)
                logger.info(f"Validated payload: {validate_payload}")
                answer = await ask_user(websocket, project_details, validate_payload)
                logger.info(f"Answer from ask_user: {answer}")

                model_op = nlp_response(answer)

                await websocket.send_text(model_op + " Thanks for using this app. Need anything, feel free to ask!")
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Exception: {e}")
        await websocket.send_text(json.dumps({"Response": "An error occurred. Please try again."}))


