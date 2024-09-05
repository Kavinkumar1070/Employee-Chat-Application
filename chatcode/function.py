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

def choose_json(role):
    json_file = ['admin','employee','teamlead','onboard']                                                 
    for i in json_file:
        if i == role:
            return i +'.json'

def sanitize_json_string(response_text: str) -> str:
    # Remove any leading or trailing whitespace
    response_text = response_text.strip()
    
    # Match the JSON object in the response text
    json_match = re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', response_text, re.DOTALL)
    
    if json_match:
        json_string = json_match.group(0)
        # Remove any unnecessary escape characters (e.g., \_)
        json_string = re.sub(r'\\_', '_', json_string)
        
        try:
            # Validate and return formatted JSON
            parsed_json = json.loads(json_string)
            return json.dumps(parsed_json, indent=4)
        except json.JSONDecodeError:
            return "{}"
    return "{}"

async def get_project_details(websocket: WebSocket,query,jsonfile):
    file = jsonfile
    with open(file, 'r') as f:
        json_config = json.load(f)
        project_names = json_config.keys()
        projectinfo ={}
        for i in project_names:
            projectinfo[i] = json_config[i]['project description']
            projectinfo
        
    client = Groq(api_key="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")
    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an AI assistant trained to extract the project name from a user query based on the provided project descriptions.

                Steps to follow:
                1.Correct any grammatical or spelling errors in the query.
                2.the details {projectinfo} have an pair of title{projectinfo.keys()} and description{projectinfo.values()}.
                3.understand available project titles and its respective description from details.
                4.Analyze the user query: "{query}" to capture the related project title based on description.
                5.capture project name based on description.If the project name matches, return the project name.
                6.If you are not sure about the project name from user query, must return 'None'.
                7.The project name must be either  'None' or from {projectinfo.keys()}.
                Do not make any assumptions by yourself.
                Return the project name in JSON format within this symbol "~~~" as shown in the examples below:

                query:"how to cancel leave"
                ~~~{{
                    "project": "None"
                }}~~~
                
                """
            },
            {
                "role": "user",
                "content": f"Extract the project name from the following query: {query} and Project Titles and Descriptions : {projectinfo}."
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
    print("project_name :",project_name)
    if project_name == "None" or project_name is None:
        await websocket.send_text("You have asked for irrelavant query ask anything from listed :")
        user_input = await websocket.receive_text()
        user_input_data = json.loads(user_input)
        query = user_input_data.get("message")
        project = await get_project_details(websocket,query,jsonfile)
        return project
    else:
        return query, project_name

def get_project_script(project_name,jsonfile): 
    file = jsonfile
    with open(file, 'r') as f:
        json_config = json.load(f)
    return json_config.get(project_name)

def split_payload_fields(project_detail):
    payload_detail = project_detail['payload']
    return payload_detail

async def fill_payload_values(websocket, query: str, payload_details: dict,jsonfile) -> Dict[str, Any]:    
    client = Groq(api_key="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")

    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""You are an expert in filling payload values from the user query and configuration file as follows:

                        Steps to Process:
                        
                        Identify Payload Fields: Extract the fields listed in {payload_details.keys()} that need to be filled.
                        Use Configuration File: Refer to the configuration file {payload_details} to understand the details of each field, such as description, data types, formats, choices, and default values.
                        Analyze User Query: Examine the user query {query} to capture values for the payload fields based on their descriptions.
                        No Assumptions: Do not make any assumptions. Return None only if there is no relevant information provided in the user query and no default value is specified in the configuration file.
                        Match Formats and Choices: Ensure that the captured values match the required formats or choices exactly. If a value does not match, use the default value specified in the configuration file.
                        Use Default Values: If the user query does not provide a value that matches the required format or choice, use the default value from the configuration file if specified. For example, if the configuration file specifies "default": "None", return "None" if no valid input is found.
                        Date Handling: For date fields, use the year 2024 if the user does not specify the year clearly.
                        Strict Data Capture: Do not use values from provided examples. Capture values only from the user query or use the default values from the configuration file.
                        JSON Response Format: Return only the payload JSON response in the FOLLOWING FORMAT, enclosed with ~~~ before and after the response.
                    
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
                    Just like above format return response
                """
            },
            {
                "role": "user",
                "content": f"Analyze the following query: {query} with config file: {payload_details} to extract and verify the details."
            }
        ]
    )

    response_text = response.choices[0].message.content.strip()
    #print("response_text: ",response_text)
    json_start_idx = response_text.find("~~~")
    json_end_idx = response_text.rfind("~~~") + 1
    result = response_text[json_start_idx:json_end_idx]
    # Sanitize the response
    sanitized_response = sanitize_json_string(result)
    logger.info(f"Sanitized response: {sanitized_response}")
    try:
        # Try to parse the JSON response
        result = json.loads(sanitized_response)
        print("*********************")
        print(result)
        print("*********************")
        response_config = result.get('payload', {})
        logger.info(f"Response config: {result}")
        print("*********************")

    except (ValueError, json.JSONDecodeError) as e:
        #await websocket.send_text(f"Error parsing JSON in fill_payload_values: {e}")
        await websocket.send_text("Model Issue. Can you please try again :")
        user_input = await websocket.receive_text()
        user_input_data = json.loads(user_input)
        user_message = user_input_data.get("message")
        query, project_name = await get_project_details(websocket,user_message,jsonfile)
        project_details = get_project_script(project_name)
        payload_details = split_payload_fields(project_details)
        filled_cleaned = await fill_payload_values(websocket, query, payload_details)
        return filled_cleaned
    return response_config


def validate(payload_detail, response_config):
    
    #print(payload_detail)
    #print('@@@@@@@@@@@@@@@@@@@@@@')
    #print(response_config)
    
    payload_details = payload_detail['payload']
    validated_payload = {}

    for key, values in payload_details.items():
        if key in response_config.keys():
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
            elif datatype == 'integer':
                try:
                    # Try to cast the value to an integer
                    int(value)
                except ValueError:
                    validated_payload[key] = None
                    continue
            elif datatype == 'mobile':
                try:
                    # Check if the value is an integer and has 10 digits
                    int_value = int(value)
                    if len(str(int_value)) != 10:
                        validated_payload[key] = None
                        continue
                except ValueError:
                    validated_payload[key] = None
                    continue
            
            # If all checks pass, keep the value
            validated_payload[key] = value
        
    final_response = {
        'project': payload_detail['project'],
        'url': payload_detail['url'],
        'method': payload_detail['method'],
        'payload': validated_payload
    }
    return final_response



def correction_update_name(names, update_fields):    
    client = Groq(api_key="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")

    # Convert dict_keys to list for easier manipulation
    update_payload_list = list(update_fields)

    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f""""You are a spelling correction expert. You have a list of valid names: {update_payload_list}.
                    The user has provided the following names to check: {names}.
                    Correct the names in the payload based on the valid names list. If a name in the payload matches a name in the list, return it as is.
                    If a name does not match any name in the list, do not return it.
                    Output only the selected values in the list like this ["employee id","details"].
                    No need of any explanations
                    Response Format: Return list response in the following format, enclosed with ~~~ before and after the response.


                """
            },
            {
                "role": "user",
                "content": f"Analyze the following list of names: {names} and fields: {update_payload_list}."
            }
        ]
    )
    response_text = response.choices[0].message.content.strip()
    json_start_idx = response_text.find("~~~") +3
    json_end_idx = response_text.rfind("~~~") 
    result = response_text[json_start_idx:json_end_idx].strip()
    response = json.loads(result)
    return response

async def update_process_with_user_input(websocket: WebSocket,project_details:dict, data: dict):
    update_payload = data['payload']
    
    # Send available fields to the user
    available_fields = list(update_payload.keys())
    await websocket.send_text(f"Enter the field names you want to update, separated by commas {available_fields}: ")
    
    # Receive field names from the user
    fields_input = await websocket.receive_text()
    fields_to_update = [field.strip() for field in fields_input.split(',')]
    
    update_fields = data['payload'].keys()
    verified_fields = correction_update_name(fields_to_update, update_fields)
    updated_fields = {}
    for i in verified_fields:
        updated_fields[i] = 'None'
    
    #print('updated_fields:',updated_fields)
    up = {'payload':updated_fields}
    #print('new updated_fields:',up)

    response  = await ask_user(websocket, project_details, up)
    #print('respones:',response)
    return response
    

async def update_process(websocket: WebSocket, project_details:dict,data: dict):
    update_payload = data['payload']
    if all(value is None or value == "None"  for value in update_payload.values()):
        print('start1')
        updated_details = await update_process_with_user_input(websocket,project_details, data)
        print("update output:",updated_details)
        return updated_details
    else:
        print('start2')
        details = await ask_user(websocket,project_details, data)
        print("update output direct:",details)
        return details
    
    
async def ask_user(websocket: WebSocket, pro, pay):
    abc = pay['payload'].copy()
    for key, value in abc.items():
        if value is None or value == "None":
            des = pro['payload'][key]['description']
            logger.info(f"Sending description to client for {key}: {des}")
            await websocket.send_text(f"Please provide: {des}")
            logger.info("Message sent to WebSocket, waiting for response...")
            user_input = await websocket.receive_text()
            user_input_data = json.loads(user_input)
            abc[key] = user_input_data.get("message")
            valid = validate(pro, abc)
            if valid['payload'][key] is None:
                return await ask_user(websocket, pro, valid)
            else:
                pay['payload'][key] = abc[key]
    return pay

def nlp_response(answer):       
    client = Groq(api_key="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")
    response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an AI assistant good at writing response for user understanding manner from dictionary to string with meaningful manner.
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