import re
import datetime
import logging
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)

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

def validate_input(field, value, datatype):
    logger.info(f"Validating {field} with value: '{value}' and datatype: {datatype}")

    if datatype == "string":
        return isinstance(value, str) and len(value.strip()) > 0

    elif datatype == "date":
        try:
            # Strip any leading/trailing spaces
            value = value.strip()
            # Validate the date format
            datetime.datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            logger.warning(f"Date validation failed for value: '{value}'")
            return False

    elif datatype == "integer":
        return value.isdigit()

    elif datatype == "email":
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, value) is not None

    elif datatype == "mobile":
        return value.isdigit() and len(value) == 10

    elif datatype == "gender":
        return value.lower() in ['male', 'female', 'other']

    elif datatype == "maritalstatus":
        return value.lower() in ['single', 'married', 'divorced', 'widowed']

    return False

async def collect_user_input(websocket: WebSocket, jsonfile, validate_input):
    res = {}

    for field, props in jsonfile.items():
        while True:
            # Prepare the message for the user
            if props['datatype'] == 'gender':
                options = " (options: Male, Female, Other)"
                message = f"Please provide {field}{options}: "
            elif props['datatype'] == 'maritalstatus':
                options = " (options: Single, Married, Divorced, Widowed)"
                message = f"Please provide {field}{options}: "
            else:
                message = f"Please provide {field} ({props['datatype']}): "

            # Send the message to the WebSocket client
            await websocket.send_text(message)
            logger.info(f"Message sent to WebSocket: {message}")

            try:
                # Receive and extract the user input from JSON payload
                user_input_json = await websocket.receive_text()
                user_input_data = json.loads(user_input_json)
                user_input = user_input_data.get("message", "").strip()
                logger.info(f"Received user input: '{user_input}'")
            except Exception as e:
                logger.error(f"Error receiving input: {e}")
                await websocket.send_text("Error receiving input. Please try again.")
                continue

            # Validate the extracted user input
            if validate_input(field, user_input, props['datatype']):
                if props['datatype'] == "integer":
                    user_input = int(user_input)
                res[field] = user_input
                break
            else:
                error_message = f"Invalid input for {field}. Please enter a valid {props['datatype']}."
                await websocket.send_text(error_message)
                logger.info(error_message)

    logger.info(f"Collected Information: {res}")
    return res
