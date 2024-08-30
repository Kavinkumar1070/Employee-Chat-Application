from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
import json
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.backend.function import collect_user_input, validate_input

jsonfile = {
    'firstname': {'datatype': 'string'},
    'lastname': {'datatype': 'string'},
    'dateofbirth': {'datatype': 'date'},
    'contactnumber': {'datatype': 'mobile'},
    'emailaddress': {'datatype': 'email'},
    'address': {'datatype': 'string'},
    'nationality': {'datatype': 'string'},
    'gender': {'datatype': 'gender'},
    'maritalstatus': {'datatype': 'maritalstatus'}
}

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.mount("/templates", StaticFiles(directory="templates"), name="templates")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            user_message = data_json.get("message")

            if user_message and user_message.lower() == 'onboard':
                await websocket.send_text(f"You said: {user_message}")
                details = await collect_user_input(websocket, jsonfile, validate_input)
                await websocket.send_text("Thanks for using this app. Need anything, feel free to ask!")
            else:
                await websocket.send_text("Goodbye, Thanks for using our app!")
                break

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Exception: {e}")
        await websocket.send_text(json.dumps({"Response": "An error occurred. Please try again."}))
