import re
from chat_bot.models import User


def validate_field_logic(field, value):
    # Perform field-specific validations logic here
    if field == 'first_name':
        min_length, max_length = 2, 50
        if not value:
            return 'First name is required.'
        elif not value.isalpha():
            return 'First name should contain only alphabetic characters'
        elif not (min_length <= len(value) <= max_length):
            return f'First name should be between {min_length} and {max_length} characters'
        elif not re.match("^[a-zA-Z-]+$", value):
            return 'First name can only contain letters and hyphens.'
        elif '  ' in value:
            return 'First name cannot contain consecutive spaces.'
        else:
            return 'First name valid'
    elif field == 'last_name':
        min_length, max_length = 2, 50
        if not value:
            return 'Last name is required.'
        elif not value.isalpha():
            return 'Last name should contain only alphabetic characters'
        elif not (min_length <= len(value) <= max_length):
            return f'Last name should be between {min_length} and {max_length} characters'
        elif not re.match("^[a-zA-Z-]+$", value):
            return 'Last name can only contain letters and hyphens.'
        elif '  ' in value:
            return 'Last name cannot contain consecutive spaces.', 401
        else:
            return 'Last name valid'
    elif field == 'phone_number':
        min_length, max_length = 10, 15
        if not value:
            return 'Phone number is required.'
        elif not re.match("^[0-9]+$", value):
            return 'Phone number can only contain numbers.'
        elif not min_length <= len(value) <= max_length:
            return f'Phone number must be between {min_length} and {max_length} digits long.'
        elif value.startswith('0'):
            return 'Phone number cannot start with a leading zero.'
        else:
            return 'Phone is valid'
    elif field == 'email':
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        allowed_domains = ['example.com', 'gmail.com', 'kabarak.ac.ke']
        if not value:
            return 'Email is required.'
        elif User.query.filter_by(email=value).first():
            return 'That email is already registered.'
        elif not re.match(email_pattern, value):
            return 'Invalid email format.'
        elif value.split('@')[1] not in allowed_domains:
            return 'Invalid email domain.'
        else:
            return 'Email is valid.'
    elif field == 'username':
        if not value:
            return 'Username is required.'
        elif User.query.filter_by(username=value).first():
            return 'Username is already taken.'
        elif not value[0].isalpha():
            return 'Username must start with a letter.'
        elif not value.isalnum():
            return 'Username can only contain letters and numbers.'
        else:
            return 'Username is valid.'
    elif field == 'password':
        special_characters = "!@#$%^&*()-_+=<>,.?/:;{}[]|"
        consecutive_char = {''.join(chr(ord(c) + i) for i in range(3)) for c in 'abcdefghijklmnopqrstuvwxyz'} | {
            ''.join(str(i) for i in range(3))}
        min_length, max_length = 8, 20
        if not value:
            return 'Password is required.'
        elif not any(char.isupper() for char in value):
            return 'Password must contain at least one uppercase letter.'
        elif not any(char.islower() for char in value):
            return 'Password must contain at least one lowercase letter.'
        elif not any(char.isdigit() for char in value):
            return 'Password must contain at least one digit.'
        elif not any(char in special_characters for char in value):
            return 'Password must contain at least one special character (!@#$%^&*()-_+=<>,.?/:;{}[]|).'
        # elif value.lower() in value.lower():
        #     return 'Password cannot contain the username.'
        elif any(consecutive in value.lower() for consecutive in consecutive_char):
            return 'Password cannot contain consecutive characters (e.g., "abc", "123").'
        elif any(value.count(char * 2) for char in value):
            return 'Password cannot contain repeated characters (e.g., "aa", "111").'
        elif len(value) < min_length:
            return f'Password must be at least {min_length} characters long.'
        elif len(value) > max_length:
            return f'Password must be at most {max_length} characters long.'
        else:
            return 'Password valid.'
    else:
        return 'Validation successful.'
