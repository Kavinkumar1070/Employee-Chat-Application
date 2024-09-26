from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from src.core.database import get_db, engine,SessionLocal
from src import models
from src.routers import personal, employee, role,leave,admin,general
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
from chatcode.onbapi_call import *
from chatcode.groq_function import *
from chatcode.onbfunction import collect_user_input, validate_input,get_jsonfile
import asyncio

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/templates", StaticFiles(directory=Path(__file__).resolve().parent / "templates"), name="templates")

app.include_router(personal.router)
app.include_router(employee.router)
app.include_router(role.router)
app.include_router(leave.router)
app.include_router(admin.router)
app.include_router(general.router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])




def update_yearly_leave_balances(db: Session):
    employees = db.query(models.EmployeeOnboarding).all()

    for employee in employees:
        # Get the role of the employee and associated leave quotas
        employment_details = db.query(models.EmployeeEmploymentDetails).filter(
            models.EmployeeEmploymentDetails.employee_id == employee.employment_id
        ).first()

        if not employment_details or not employment_details.role_id:
            continue

        role = db.query(models.Role).filter(models.Role.id == employment_details.role_id).first()
        if not role:
            continue

        # Get the employee's leave calendar
        leave_calendar = db.query(models.LeaveCalendar).filter(
            models.LeaveCalendar.employee_id == employee.employment_id
        ).first()

        if not leave_calendar:
            continue

        # Update leave balances based on the role's leave quotas
        leave_calendar.sick_leave = role.sick_leave
        leave_calendar.personal_leave = role.personal_leave
        leave_calendar.vacation_leave = role.vacation_leave
        leave_calendar.unpaid_leave = 0

        try:
            db.commit()  # Commit the updated leave balances
            db.refresh(leave_calendar)
        except Exception as e:
            db.rollback()  # Roll back in case of error
            logging.error(f"Error updating leave for employee {employee.employment_id}: {str(e)}")

# Scheduler to run the task every year
def start_scheduler():
    scheduler = BackgroundScheduler()

    # Schedule the task to run once a year (January 1st)
    scheduler.add_job(
        update_yearly_leave_balances,
        trigger='cron',
        year='*',
        month='1',
        day='1',
        args=[SessionLocal()]  # Pass a fresh DB session each time
    )
    
    scheduler.start()

# FastAPI startup event
@app.on_event("startup")
async def on_startup():
    # Start the scheduler in the background
    start_scheduler()


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
                details = await collect_user_input(websocket, file, validate_input)
                details['dateofbirth'] = datetime.strptime(details['dateofbirth'], '%Y-%m-%d').strftime('%Y-%m-%d')
                details['contactnumber'] = int(details['contactnumber'])
                print('*****************************')
                print(details)
                print('*****************************')
                response = await onboard_personal_details(websocket,details)
                print(response)
                if response != "Email Send Successfully":
                    await websocket.send_text(response)
                    await websocket.send_text("You will be Navigated to Login Screen")  # Redirect to the new page
                    await asyncio.sleep(3)  # Add a 3-second delay
                    await websocket.send_text("navigate")
                    break
                else:
                    await websocket.send_text("Your details have been saved successfully. Check your personal mail for Username and Password.")
                    await websocket.send_text("You will be Navigated to Login Screen")  # Redirect to the new page
                    await asyncio.sleep(3)  # Add a 3-second delay
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
            try:
                # Receiving data
                data = await websocket.receive_text()
                data_json = json.loads(data)
                print('________________________________________________________________________________________')
                print("data json :", data_json)
                print('________________________________________________________________________________________')

                token = data_json.get("token")
                user_message = data_json.get("message")
                role = data_json.get("role")
                apikey = data_json.get('apikey')
                model = data_json.get('model')

                # Check for 'quit' message
                if user_message.lower() == 'quit':
                    await websocket.send_text("Goodbye, Thanks for using our app!")
                    await asyncio.sleep(3)
                    await websocket.send_text("quit")
                    break
                
                # Main logic
                jsonfile = choose_json(role)
                response = await get_project_details(websocket, user_message, jsonfile,apikey,model)
                query = response[0]
                project_name = response[1]
                print('________________________________________________________________________________________')
                print('Query amd Project name') 
                print(query)
                print(project_name)
                if isinstance(project_name, str) and project_name == "Groq API error":
                        await websocket.send_text("Error: Failed to process the response from Groq API.")
                        await asyncio.sleep(3)
                        await websocket.send_text('navigateerror')
                        continue
                print('________________________________________________________________________________________')
                project_details = get_project_script(project_name, jsonfile)
                print('________________________________________________________________________________________')
                print('Project Details') 
                print(project_details)
                print('________________________________________________________________________________________')
                payload_details = split_payload_fields(project_details)
                print('________________________________________________________________________________________')
                print('Payload Details') 
                print(payload_details)
                print('________________________________________________________________________________________')
                if payload_details != {}:
                    print('________________________________________________________________________________________')
                    print('Payload Detail is Not Empty')
                    filled_cleaned = await fill_payload_values(websocket, query, payload_details, apikey,model)
                    # Check if response indicates a Groq API error
                    if isinstance(filled_cleaned, str) and filled_cleaned == "Groq API error":
                        await websocket.send_text("Error: Failed to process the response from Groq API.")
                        await asyncio.sleep(3)
                        await websocket.send_text('navigateerror')
                        continue
                else:
                    print('________________________________________________________________________________________')
                    print('Payload Detail is Empty')
                    filled_cleaned = payload_details
                        
                
                validate_payload = validate(project_details, filled_cleaned) 
                print('Validate Payload') 
                print(validate_payload)
                print('________________________________________________________________________________________')
                
                # Handling PUT requests
                if validate_payload['method'] == 'PUT':
                    answer = await update_process(websocket, project_details, validate_payload)
                    print("---------------------------------------------------------------------------------------------------------------------------")
                    logger.info(f"Answer from update_process: {answer}")
                    print("---------------------------------------------------------------------------------------------------------------------------")
                else:
                    # Handling other requests
                    answer = await ask_user(websocket, project_details, validate_payload)
                    print("---------------------------------------------------------------------------------------------------------------------------")
                    logger.info(f"Answer from ask_user: {answer}")
                    print("---------------------------------------------------------------------------------------------------------------------------")
                
                answer['bearer_token'] = token

                    
                
                # Database operation
                result,payload = await database_operation(websocket, answer)
                
                print('result :',result)
                print('payload :',payload)
                
                if result == "Table" and payload == "Return":
                    await websocket.send_text("Glad to help! If you need more assistance, I'm just a message away.")
                    continue
                
                elif result and payload:
                    if result == 'Internal Server Error':
                        await websocket.send_text(f"{result}. Sorry for inconvenience, try after sometime.")
                        continue
                    else:
                        model_output = await nlp_response(websocket, result, payload, apikey, model)
                        await websocket.send_text(f"{model_output}. Glad to help! If you need more assistance, I'm just a message away.")
                        continue

                
                elif result and  not payload:
                    
                    if isinstance(result, str):
                        result = json.loads(result)
                        result =  result['detail']
                        await websocket.send_text(f"{result}. Glad to help! If you need more assistance, I'm just a message away.")
                        continue
                    if 'detail' in result:
                        result =  result['detail']
                        await websocket.send_text(f"{result}. Glad to help! If you need more assistance, I'm just a message away.")
                        continue
                    else:
                        await websocket.send_text(f"check not payload")
                        continue
                
                else:
                    await websocket.send_text("Back end server error try again.")
                    await asyncio.sleep(3)
                    continue
                

                                                    
            except Exception as e:
                print('Chat error')
                await websocket.send_text(f"An error occurred: {str(e)}")


    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        await asyncio.sleep(3)
    except Exception as e:
        print('out of chat')
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}")
        await asyncio.sleep(3)
    finally:
        await websocket.close()


