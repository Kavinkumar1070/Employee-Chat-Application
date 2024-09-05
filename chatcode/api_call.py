import requests
import pyodbc
from datetime import date
from datetime import datetime
import httpx
import asyncio
from fastapi import WebSocket
from typing import Dict
import logging
import json
logger = logging.getLogger(__name__)


import httpx
from fastapi import WebSocket

import httpx
from fastapi import WebSocket
async def onboard_personal_details(websocket: WebSocket, details: Dict[str, str]):
    url = 'http://127.0.0.1:8000/personal/employees'
    payload = details
    timeout_seconds = 30  # Timeout in seconds
    

    try:
        # Initialize HTTP client with timeout
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:

            response = await client.post(url, json=payload)

            response.raise_for_status()  # Raise an exception for HTTP errors
            response_data = response.json()

            return response_data
 
    except httpx.HTTPStatusError as e:
        # Include response text in error message for better diagnostics
        error_message = f"HTTP error occurred: {str(e)} - Status Code: {e.response.status_code}\nResponse Content: {e.response.text}"
        await websocket.send_text(error_message)
        print(error_message)
        return error_message
 
    except httpx.RequestError as e:
        # General request error handling
        error_message = f"Request error occurred: {str(e)}"
        await websocket.send_text(error_message)
        print(error_message)
        return error_message
 
    except Exception as e:
        # Catch all other unexpected errors
        error_message = f"An unexpected error occurred: {str(e)}"
        await websocket.send_text(error_message)
        print(error_message)
        return error_message
    
async def onboard_personal_d(websocket: WebSocket, details: Dict[str, str]):
    url_template = details.get('url')
    payload = details.get('payload', {})
    method = details.get('method', 'GET').upper()
    timeout_seconds = 30  # Timeout in seconds

    # Bearer Token for Authorization
    bearer_token = details.get('bearer_token')

    # Check if Bearer token is provided
    if not bearer_token:
        await websocket.send_text("Bearer token is missing in the request.")
        return "Bearer token is missing."

    # Extract employee id from the payload
    
    print("222222222222222222222222222",payload)
    # Replace placeholder {employee_id} with the actual value in the URL
    try:
        # Replace placeholders in the URL template using the payload dictionary
        url = url_template.format(**payload)
        print("111111111111111111111111111111",url)
    except KeyError as e:
        missing_key = str(e).strip("'")
        await websocket.send_text(f"Missing value for placeholder: {missing_key}.")
        return f"Missing value for placeholder: {missing_key}."

    headers = {"Authorization": f"Bearer {bearer_token}"}

    # Dictionary to map HTTP methods to client functions
    method_dispatch = {
        "GET": lambda client: client.get(url, headers=headers),
        "DELETE": lambda client: client.delete(url, headers=headers),
        "PUT": lambda client: client.put(url, json=payload, headers=headers),
        "POST": lambda client: client.post(url, json=payload, headers=headers)
    }

    if method not in method_dispatch:
        await websocket.send_text(f"Unsupported HTTP method: {method}")
        return f"Unsupported HTTP method: {method}"

    try:
        # Initialize HTTP client with timeout and Bearer token in headers
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await method_dispatch[method](client)
            print('############', response)

            response.raise_for_status()  # Raise an exception for HTTP errors

            response_data = response.json()  # Parse JSON response
            print("*****", response_data)
            print(type(response_data))
            # Optionally send response back to WebSocket for feedback
            await websocket.send_text(f"Request successful: {response_data}")
            return response_data

    except httpx.HTTPStatusError as e:
        error_message = (f"HTTP error occurred: {str(e)} - "
                        f"Status Code: {e.response.status_code}\n"
                        f"Response Content: {e.response.text}")
        await websocket.send_text(error_message)
        return error_message

    except httpx.RequestError as e:
        error_message = f"Request error occurred: {str(e)}"
        await websocket.send_text(error_message)
        return error_message

    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        await websocket.send_text(error_message)
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
    
