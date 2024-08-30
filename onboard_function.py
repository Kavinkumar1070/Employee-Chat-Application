import re
import datetime


# Example JSON file structure
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


# Function to validate input based on datatype
def validate_input(field, value, datatype):
    if datatype == "string":
        return isinstance(value, str) and len(value.strip()) > 0

    elif datatype == "date":
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    elif datatype == "integer":
        return value.isdigit()

    elif datatype == "email":
        # Basic email validation using regex
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\.com$'
        return re.match(email_regex, value) is not None

    elif datatype == "mobile":
        # Ensure the mobile number is 10 digits
        return value.isdigit() and len(value) == 10

    elif datatype == "gender":
        return value.lower() in ['male', 'female', 'other']

    elif datatype == "maritalstatus":
        return value.lower() in ['single', 'married', 'divorced', 'widowed']

    return False


# Dictionary to store results
res = {}

# Loop through each field and get input from the user
for field, props in jsonfile.items():
    while True:
        if props['datatype'] in ['gender', 'maritalstatus']:
            if props['datatype'] == 'gender':
                options = " (options: Male, Female, Other)"
            elif props['datatype'] == 'maritalstatus':
                options = " (options: Single, Married, Divorced, Widowed)"
            user_input = input(f"Please provide {field}{options}: ")
        else:
            user_input = input(f"Please provide {field} ({props['datatype']}): ")

        if validate_input(field, user_input, props['datatype']):
            if props['datatype'] == "integer":
                user_input = int(user_input)  # Convert to integer
            res[field] = user_input
            break
        else:
            print(f"Invalid input for {field}. Please enter a valid {props['datatype']}.")

print("Collected Information:")
print(res)
