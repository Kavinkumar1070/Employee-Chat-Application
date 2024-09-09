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


async def get_project_details(websocket: WebSocket, query: str, jsonfile: str):
    projectinfo = {}
    
    try:
        with open(jsonfile, 'r') as f:
            json_config = json.load(f)
            project_names = json_config.keys()
            for i in project_names:
                projectinfo[i] = json_config[i]['project description']
    
    except FileNotFoundError:
        print("Error: The file was not found.")
        await websocket.send_text("Error: The configuration file was not found.")
        return None

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")
        await websocket.send_text("Error: Failed to read the configuration file.")
        return None

    client = Groq(api_key="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")
    
    try:
        response = client.chat.completions.create(
            model='mixtral-8x7b-32768',
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are an AI assistant trained to extract the project name from a user query based on the provided project descriptions.

                    Steps to follow:
                    1. Correct any grammatical or spelling errors in the query.
                    2. The details {projectinfo} have a pair of title {list(projectinfo.keys())} and description {list(projectinfo.values())}.
                    3. Understand available project titles and their respective descriptions from details.
                    4. Analyze the user query: "{query}" to capture the related project title based on the description.
                    5. Capture the project name based on the description. If the project name matches, return the project name.
                    6. If you are not sure about the project name from the user query, return 'None'.
                    7. The project name must be either 'None' or from {list(projectinfo.keys())}.
                    Do not make any assumptions by yourself.
                    Return the project name in JSON format within these symbols "~~~" as shown in the examples below:

                    query: "how to cancel leave"
                    ~~~
                    {{
                        "project": "None"
                    }}
                    ~~~
                    """
                },
                {
                    "role": "user",
                    "content": f"Extract the project name from the following query: {query} and Project Titles and Descriptions: {projectinfo}."
                }
            ]
        )
    
    except Exception as e:
        print(f"Error during API call: {e}")
        await websocket.send_text("Error: Failed to process the query.")
        return None

    try:
        response_text = response.choices[0].message.content.strip()
        json_start_idx = response_text.find("~~~")
        json_end_idx = response_text.rfind("~~~") + 1
        result = response_text[json_start_idx:json_end_idx]
        result = sanitize_json_string(result)
        project_name = json.loads(result).get("project")
        
        if project_name == "None" or project_name is None:
            await websocket.send_text("You have asked for an irrelevant query. Ask anything from the listed projects:")
            user_input = await websocket.receive_text()
            user_input_data = json.loads(user_input)
            query = user_input_data.get("message")
            return await get_project_details(websocket, query, jsonfile)
        
        return query, project_name

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the response.")
        await websocket.send_text("Error: Failed to process the response.")
        return None

    except Exception as e:
        print(f"Error while processing the response: {e}")
        await websocket.send_text("Error: An unexpected error occurred.")
        return None

def get_project_script(project_name: str, jsonfile: str):
    try:
        with open(jsonfile, 'r') as f:
            json_config = json.load(f)
            project_script = json_config.get(project_name)
            print("*****************************************************")
            print("project_detail Done")
            return project_script
    
    except FileNotFoundError:
        print("Error: The file was not found.")
        return "Error: The configuration file was not found."
    
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")
        return "Error: Failed to read the configuration file."

def split_payload_fields(project_detail: dict):
    try:
        payload_detail = project_detail['payload']
        print("*****************************************************")
        print("payload_detail Done")
        return payload_detail

    except KeyError as e:
        print(f"Error: Missing expected key in project details: {e}")
        return "Error: Missing expected key in project details."
    
    except TypeError:
        print("Error: The project detail provided is not a dictionary.")
        return "Error: Invalid project detail format."


async def fill_payload_values(websocket: WebSocket, query: str, payload_details: dict, jsonfile: str) -> Dict[str, Any]:
    client = Groq(api_key="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")

    try:
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
                    NO ASSUMPTIONS: Do not make any assumptions. Return None only if there is no relevant information provided in the user query and no default value is specified in the configuration file.
                    Match Formats and Choices: Ensure that the captured values match the required formats or choices exactly. If a value does not match, use the default value specified in the configuration file.
                    Use Default Values: If the user query does not provide a value that matches the required format or choice, use the default value from the configuration file if specified. For example, if the configuration file specifies "default": "None", return "None" if no valid input is found.
                    Strict Data Capture: Do not use values from provided examples. Capture values only from the user query or use the default values from the configuration file.
                    JSON Response Format: Return only the payload JSON response in the following format, enclosed with ~~~ before and after the response.

                Example output format:
                    query 1: like to apply leave for my employee id 25 from july 24 to july 25.
                    ~~~{{
                        "payload": {{
                            "empid": "None",
                            "startdate": "None",
                            "enddate": "None", 
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
                Do NOT make any assumptions by yourself.
                """
                },
                {
                    "role": "user",
                    "content": f"Analyze the following query: {query} with config file: {payload_details} to extract and verify the details."
                }
            ]
        )
    
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        await websocket.send_text("Error: Failed to process the query. Please try again.")
        return {}

    try:
        response_text = response.choices[0].message.content.strip()
        json_start_idx = response_text.find("~~~")
        json_end_idx = response_text.rfind("~~~") + 1
        result = response_text[json_start_idx:json_end_idx]
        
        # Sanitize the response
        sanitized_response = sanitize_json_string(result)
        logger.info(f"Sanitized response: {sanitized_response}")
        
        try:
            # Try to parse the JSON response
            result = json.loads(sanitized_response)
            response_config = result.get('payload', {})
            print("*****************************************************")
            print("Fill payload Done")
            print(result)
            return response_config
        
        except json.JSONDecodeError:
            logger.error("Error: Failed to decode JSON from the response.")
            await websocket.send_text("Error: The response format is incorrect. Please try again.")
            return {}
        
    except Exception as e:
        logger.error(f"Error while processing the response: {e}")
        await websocket.send_text("Error: An unexpected error occurred. Please try again.")
        return {}



def validate(payload_detail, response_config):
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
    print("Validation Done")
    print(final_response)
    print("*****************************************************")
    return final_response

def correction_update_name(names, update_fields):
    try:
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
        json_start_idx = response_text.find("~~~") + 3
        json_end_idx = response_text.rfind("~~~")
        result = response_text[json_start_idx:json_end_idx].strip()

        # Try to parse the result to JSON, handle any parsing errors
        try:
            response = json.loads(result)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return []  # Return an empty list in case of parsing failure

        return response

    except Exception as e:
        print(f"Error occurred in correction_update_name: {e}")
        return []  # Return an empty list in case of any unexpected failure


async def update_process_with_user_input(websocket: WebSocket, project_details: dict, data: dict):
    try:
        update_payload = data['payload']
        
        # Send available fields to the user
        available_fields = list(update_payload.keys())
        await websocket.send_text(f"Enter the field names you want to update, separated by commas {available_fields}: ")
        
        # Receive field names from the user
        fields_input = await websocket.receive_text()
        fields_input = json.loads(fields_input)
        fields_input = fields_input.get('message')
        
        print('fields_input  :',fields_input)
        
        # Handle the case where the user might not input anything or input invalid data
        if not fields_input:
            await websocket.send_text("No fields provided. Please try again.")
            return None
        #if len(fields_input) != 1:
        fields_to_update = [field.strip() for field in fields_input.split(',')]
        #else:
        #    fields_to_update = [fields_input.strip()]
        
        update_fields = update_payload.keys()
        verified_fields = correction_update_name(fields_to_update, update_fields)

        if not verified_fields:
            await websocket.send_text("No valid fields to update. Please try again.")
            return None
        
        # Initialize updated fields with 'None'
        updated_fields = {}
        for i in verified_fields:
            updated_fields[i] = 'None'
        
        up = {'payload': updated_fields}
        print('new updated_fields:', up)

        response = await ask_user(websocket, project_details, up)
        return response

    except Exception as e:
        print(f"Error occurred in update_process_with_user_input: {e}")
        await websocket.send_text("An error occurred while processing your request. Please try again.")
        return None


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