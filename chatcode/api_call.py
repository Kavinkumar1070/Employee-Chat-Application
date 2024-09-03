import requests
import pyodbc
from datetime import date
from datetime import datetime
import httpx
import asyncio
from fastapi import WebSocket
import logging
import json
logger = logging.getLogger(__name__)


import httpx
from fastapi import WebSocket

import httpx
from fastapi import WebSocket

async def onboard_personal_details(websocket: WebSocket, det: dict):
    url = 'http://127.0.0.1:8000/personal/employees'
    payload = det
    try:
        print('Trying to send request')
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_str = json.dumps(response_data)

        print('Response:', response_str)

        await websocket.send_text(str(response_str))

        return response_str

    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error occurred: {str(e)}"
        await websocket.send_text(error_message)
        print(error_message)
        return error_message

    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        await websocket.send_text(error_message)
        print(error_message)
        return error_message



# def post_permission(answer):
#     url = answer['url']
#     method = answer['method']
#     payload = answer['payload']
#     if method == 'GET':
#         response = requests.get(url)
#         permission_data = response.json()
#         return permission_data
#     elif method == 'POST':
#         response = requests.post(url, json=payload)
#         permission_data = response.json()
#         return permission_data
#     else:
#         permission_data = {"response":"method not identified"}
#         return permission_data
    

    
# # Function to get joke
# def get_joke(type: str):
#     url = f'https://official-joke-api.appspot.com/jokes/{type}/random'
#     response = requests.get(url)
#     if response.status_code == 200:
#         joke_data = response.json()
#         return joke_data
#     else:
#         return f"Failed to retrieve joke. Status code: {response.status_code}"

# # Function to get weather
# def get_weather(api_key: str, city: str):
#     base_url = "http://api.weatherapi.com/v1/current.json"
#     complete_url = f"{base_url}?key={api_key}&q={city}&aqi=no"
#     response = requests.get(complete_url)
#     data = response.json()
    
#     if 'error' not in data:
#         current = data["current"]
#         condition = current["condition"]
        
#         temperature = current["temp_c"]
#         pressure = current["pressure_mb"]
#         humidity = current["humidity"]
#         weather_description = condition["text"]
        
#         weather_report = {
#             "Temperature": temperature,
#             "Pressure": pressure,
#             "Humidity": humidity,
#             "Description": weather_description
#         }
#         print("weather_report")
#         return weather_report
#     else:
#         return {"error": data['error']['message']}


# def apply_leave(emp_id, start_date, end_date, reason):
#     conn = None
#     try:
#         # Connect to the MSSQL database
#         conn = pyodbc.connect(
#             f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=CONVERSE\SQLEXPRESS01;DATABASE=chinook;UID=kavintest;PWD=kavin00031'
#         )
#         cursor = conn.cursor()

#         # Insert the leave request into the leave_requests table
#         cursor.execute('''
#             INSERT INTO leave_requests (emp_id, start_date, end_date, reason, status)
#             VALUES (?, ?, ?, ?, 'Pending')
#         ''', (emp_id, start_date, end_date, reason))

#         # Commit the transaction
#         conn.commit()

#         return f'Leave request applied successfully for employee with details emp_id:{emp_id}, start_date:{start_date}, end_date:{end_date}, reason:{reason}.'

#     except pyodbc.Error as e:
#         return f'Failed to apply leave request: {e}'

#     finally:
#         if conn:
#             conn.close()
            

# def cancel_leave( leave_id, cancel_reason):
#     conn = None
#     try:
#         # Connect to the MSSQL database
#         conn = pyodbc.connect(
#             f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=CONVERSE\SQLEXPRESS01;DATABASE=chinook;UID=kavintest;PWD=kavin00031'
#         )
#         cursor = conn.cursor()

#         # Update the leave request status to 'Cancelled' and add the cancel reason
#         cursor.execute('''
#             UPDATE leave_requests
#             SET status = 'Cancelled', reason = ?
#             WHERE leave_id = ?
#         ''', (cancel_reason, leave_id))

#         # Commit the transaction
#         conn.commit()

#         if cursor.rowcount > 0:
#             return f'Leave request cancelled successfully for employee with details leave_id:{leave_id}, cancel_reason:{cancel_reason}.'
#         else:
#             return 'Failed to cancel leave request: Leave ID not found.'

#     except pyodbc.Error as e:
#         return f'Failed to cancel leave request: {e}'

#     finally:
#         if conn:
#             conn.close()



    
  