import json
import re
import logging
from typing import Any, Dict
from datetime import datetime
from fastapi import WebSocket
import groq
from groq import Groq

import logging
from fastapi import WebSocket

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

def sanitize_json_string(response_text: str) -> str:
    # Remove any leading or trailing whitespace
    response_text = response_text.strip()
    
    # Match the JSON object in the response text
    json_match = re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', response_text, re.DOTALL)
    
    if json_match:
        return json_match.group(0)
    return "{}"

async def get_project_details(websocket: WebSocket,query):
    file = 'config.json'
    with open(file, 'r') as f:
        json_config = json.load(f)
        project_names = json_config.keys()
        
    client = Groq(api_key="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")
    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an AI assistant trained to extract the project name from a user query based on the configuration file project description.
                steps to follow:
                    1.Understand the project based on configuration file {json_config} project description. 
                    2.Correct Grammatical and spelling error in query.
                    3.Analyze the user query: "{query}"  to capture the related project name specified here {project_names} based on understanding.
                    4.Do not bilndly use keyword match to finalize project, use your understanding.if matches return same project name else return 'None'.
                    5.if you are unsure about project name or can't able to capture name must return as 'None'.
                    6.do not make any assumptions.
                
                Return the project name in JSON format as mentioned below format:
                query:"like to cancel leave request"
                ~~~{{
                    "project": "leave cancel"
                }}~~~
                
                query:"how to cancel leave"
                ~~~{{
                    "project": "None"
                }}~~~
                
                query:'can you explain steps for apply leave request'
                ~~~{{
                    "project": "None"
                }}~~~
                
                query:'want to apply new leave request'
                ~~~{{
                    "project": "leave apply"
                }}~~~
                
                
                """
            },
            {
                "role": "user",
                "content": f"Extract the project name from the following query: {query} and use this configuration: {json_config}and projectr names {project_names}."
            }
        ]
    )
    response_text = response.choices[0].message.content.strip()
    #print(response_text)
    json_start_idx = response_text.find("~~~")
    json_end_idx = response_text.rfind("~~~") + 1
    result = response_text[json_start_idx:json_end_idx]
    result = sanitize_json_string(result)
    project_name = json.loads(result).get("project")
    if project_name == "None" or project_name is None:
        await websocket.send_text("You have provided irrelavant query to use case pass relevant one please :")
        user_input = await websocket.receive_text()
        user_input_data = json.loads(user_input)
        query = user_input_data.get("message")
        project = await get_project_details(websocket,query)
        return project
    else:
        return query, project_name

def get_project_script(project_name): 
    file = 'config.json'
    with open(file, 'r') as f:
        json_config = json.load(f)
    return json_config.get(project_name)

def split_payload_fields(project_detail):
    payload_detail = project_detail['payload']
    return payload_detail

async def fill_payload_values(websocket, query: str, payload_details: dict) -> Dict[str, Any]:    
    client = Groq(api_key="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")

    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""You are an expert in filling payload values from the user query and configuration file as follows:
                Steps to process:
                    1. {payload_details.keys()} are the payload fields need to determine.
                    2. Use configuration file  {payload_details} to know the fields details like description, data types, formats, choices, defaults are used to fill payload field values.
                    3. Analyze the user query {query} to capture the payload field values based on description.
                    4. DO NOT MAKE ANY ASSUMPTIONS BY YOURSELF, RETURN DEFAULT VALUES FOR UNKNOWN FIELDS.
                    5. Ensure that the fields captured match the required format or choices exactly, else use default values.
                    6. If the user query does not provide enough information related to description or you are not sure about values after analysing user query ,then use the default field values.
                    7. For date datatype, use year as 2024 if the user doesn't mention the year properly.
                    8. Do not use any values from provided Examples below , must capture from user query or use default field value from the config file.
                    9. Return only the payload JSON response without any explanation, with mentioned format ~~~ before and after response.
                    
                    Return only the JSON response with the key 'payload' as mentioned below format with ~~~.
                    Example output format:
                        query 1: like to apply leave for my employee id 25 from july 24 to july 25.
                        ~~~{{
                            "payload": {{
                                "empid": "None",
                                "startdate": "2024-07-24",
                                "enddate": "2024-07-25",
                                "reason": "None"
                            }}
                        }}~~~
                        
                        query 2: i don't want an leave on saturday for id L12.
                        ~~~{{
                            "payload": {{
                                "leaveid": "L12",
                                "reason": "None"
                            }}
                        }}~~~
                        
                        query 3: like to apply leave for my employee id cds14 from july 25 to july 24.
                        ~~~{{
                            "payload": {{
                                "empid": "cds14",
                                "startdate": "None",
                                "enddate": "None",
                                "reason": "None"
                            }}
                        }}~~~

                """
            },
            {
                "role": "user",
                "content": f"Analyze the following query: {query} with config file: {payload_details} to extract and verify the details."
            }
        ]
    )

    response_text = response.choices[0].message.content.strip()
    print("response_text: ",response_text)
    json_start_idx = response_text.find("~~~")
    json_end_idx = response_text.rfind("~~~") + 1
    result = response_text[json_start_idx:json_end_idx]
    # Sanitize the response
    sanitized_response = sanitize_json_string(result)
    logger.info(f"Sanitized response: {sanitized_response}")
    try:
        # Try to parse the JSON response
        result = json.loads(sanitized_response)
        #print(result)
        response_config = result.get('payload', {})
        logger.info(f"Response config: {response_config}")

    except (ValueError, json.JSONDecodeError) as e:
        #await websocket.send_text(f"Error parsing JSON in fill_payload_values: {e}")
        await websocket.send_text("Model Issue. Can you please try again :")
        user_input = await websocket.receive_text()
        user_input_data = json.loads(user_input)
        user_message = user_input_data.get("message")
        query, project_name = await get_project_details(websocket,user_message)
        project_details = get_project_script(project_name)
        payload_details = split_payload_fields(project_details)
        filled_cleaned = await fill_payload_values(websocket, query, payload_details)
        return filled_cleaned
    return response_config


def validate(payload_detail, response_config):
    payload_details = payload_detail['payload']
    validated_payload = {}

    for key, values in payload_details.items():
        value = response_config.get(key)
        required = values.get('required', False)
        
        # If the field is required and missing, set to None
        if value is None:
            if required:
                validated_payload[key] = None
            continue
        
        # Check datatype and format
        datatype = values['datatype']
        if datatype == 'regex':
            pattern = values['format']
            if not re.match(pattern, value):
                validated_payload[key] = None
                continue
        elif datatype == 'date':
            date_format = values['format']
            try:
                datetime.strptime(value, date_format)
            except ValueError:
                validated_payload[key] = None
                continue
        elif datatype == 'choices':
            choices = values['choices']
            if value not in choices:
                validated_payload[key] = None
                continue
        elif datatype == 'string' and value != 'None':
            if not isinstance(value, str):
                validated_payload[key] = None
                continue
        
        # If all checks pass, keep the value
        validated_payload[key] = value
    
    final_response = {
        'project': payload_detail['project'],
        'url': payload_detail['url'],
        'apikey': payload_detail['apikey'],
        'method': payload_detail['method'],
        'payload': validated_payload
    }
    return final_response

async def ask_user(websocket: WebSocket, pro, pay):
    abc = pay['payload'].copy()
    for k, v in abc.items():
        if v is None or v == "None":
            des = pro['payload'][k]['description']
            logger.info(f"Sending description to client for {k}: {des}")
            await websocket.send_text(f"Please provide: {des}")
            logger.info("Message sent to WebSocket, waiting for response...")
            user_input = await websocket.receive_text()
            user_input_data = json.loads(user_input)
            abc[k] = user_input_data.get("message")
            valid = validate(pro, abc)
            if valid['payload'][k] is None:
                return await ask_user(websocket, pro, valid)
            else:
                pay['payload'][k] = abc[k]
    return pay

def nlp_response(answer):       
    client = Groq(api_key="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")
    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an AI assistant good at writing  response for user understanding manner from dictionary to string with meaningful manner.
                convert dictionary into string as meaningful response.
                """
            },
            {
                "role": "user",
                "content": f"summarise the user response {answer}."
            }
        ]
    )
    response_text = response.choices[0].message.content.strip()
    return response_text