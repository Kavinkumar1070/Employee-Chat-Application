from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.core.database import get_db, engine
from src import models
from src.routers import personal, employee, role,leave
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
from chatcode.function import *
from chatcode.api_call import *
from chatcode.onbfunction import collect_user_input, validate_input,get_jsonfile
import asyncio

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/templates", StaticFiles(directory=Path(__file__).resolve().parent / "templates"), name="templates")


app.include_router(personal.router)
app.include_router(employee.router)
app.include_router(role.router)
app.include_router(leave.router)
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

@app.websocket("/ws/onboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            user_message = data_json.get("message", "").strip().lower()            
            print(f"Received message: '{user_message}'")  # Debugging: Log the received message

            if user_message == 'quit':
                await websocket.send_text("Please wait,You will be Navigated to Login Screen")  # Redirect to the new page
                await asyncio.sleep(3)  # Add a 3-second delay
                await websocket.send_text("navigate")  # Redirect to the new page
                break

            elif user_message == 'onboard':
                file = get_jsonfile()
                await websocket.send_text(f"You said: {user_message}")
                details = await collect_user_input(websocket, file, validate_input)
                details['dateofbirth'] = datetime.strptime(details['dateofbirth'], '%Y-%m-%d').strftime('%Y-%m-%d')
                details['contactnumber'] = int(details['contactnumber'])
                response = await onboard_personal_details(websocket,details)
                print(response)
                if response != "Email Send Successfully":
                    await websocket.send_text(response)
                    await websocket.send_text("You will be Navigated to Login Screen")  # Redirect to the new page
                    await asyncio.sleep(7)  # Add a 3-second delay
                    await websocket.send_text("navigate")
                    break
                else:
                    await websocket.send_text("Your details have been saved successfully. Check your personal mail for Username and Password.")
                    await websocket.send_text("You will be Navigated to Login Screen")  # Redirect to the new page
                    await asyncio.sleep(7)  # Add a 3-second delay
                    await websocket.send_text("navigate")
                    break
            else:
                await websocket.send_text("Please enter 'Onboard' in the chat below or 'Quit' to exit.")
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Exception: {e}")
        await websocket.send_text(json.dumps({"Response": "An error occurred. Please try again."}))


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            print("data_json",data_json)
            token = data_json.get("token")
            user_message = data_json.get("message")
            role = data_json.get("role")

            if user_message.lower() == 'quit':
                await websocket.send_text("Goodbye, Thanks for using our app!")
                break
            else:
                jsonfile = choose_json(role)
                query, project_name = await get_project_details(websocket, user_message,jsonfile)
                project_details = get_project_script(project_name,jsonfile)
                payload_details = split_payload_fields(project_details)
                filled_cleaned = await fill_payload_values(websocket, query, payload_details,jsonfile)
                #print(filled_cleaned)
                #autochecked_payload = check_autofill(query, filled_cleaned)
                validate_payload = validate(project_details, filled_cleaned)
                
                if validate_payload['method'] == 'PUT':
                    answer = await update_process(websocket,project_details,validate_payload)
                    logger.info(f"Answer from ask_user: {answer}")
                    answer['bearer_token'] = token
                else:
                    answer = await ask_user(websocket, project_details, validate_payload)
                    logger.info(f"Answer from ask_user: {answer}")
                    answer['bearer_token'] = token
                    
                result =await database_operation(websocket,answer)
                if not result:
                    await websocket.send_text(" Thanks for using this app. Need anything, feel free to ask!")
                    continue
                else:
                    model_output = nlp_response(result)
                    await websocket.send_text(model_output + " Thanks for using this app. Need anything, feel free to ask!")
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Exception: {e}")
        await websocket.send_text(json.dumps({"Response": "An error occurred. Please try again."}))



