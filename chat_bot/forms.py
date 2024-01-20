# chat_bot/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, DateTimeField, TextAreaField, SelectField, DateField, TimeField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp, Email, DataRequired
import re
from email_validator import validate_email, EmailNotValidError
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFProtect
from chat_bot.models import User


class RegistrationForm(FlaskForm):
    first_name = StringField(validators=[InputRequired(), Length(max=30),
                                         Regexp('^[a-zA-Z-]+$',
                                                message='First name can only contain letters and hyphens')],
                             render_kw={"placeholder": "First Name"})
    last_name = StringField(validators=[InputRequired(), Length(max=30),
                                        Regexp('^[a-zA-Z-]+$',
                                               message='Last name can only contain letters and hyphens')],
                            render_kw={"placeholder": "Last Name"})
    phone_number = StringField(
        validators=[InputRequired(), Regexp('^[0-9]+$', message='Phone number can only contain numbers'),
                    Length(min=10, max=15)],
        render_kw={"placeholder": "Phone Number"})
    email = StringField(validators=[InputRequired(), Email(), Length(max=50)],
                        render_kw={"placeholder": "Email"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20),
                                       Regexp('^[a-zA-Z0-9_.-]+$',
                                              message="Username can only contain letters. numbers, underscores, dots, "
                                                      "and hyphens")],
                           render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20),
                                         Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()-_+=]).*$',
                                                message="Password must contain at least one lowercase letter, "
                                                        "one uppercase letter, one digit, and one special character")],
                             render_kw={"placeholder": "password"})

    submit = SubmitField('Register')

    def validate_field_without_whitespace(self, field):
        if field.data.strip() != field.data:
            raise ValidationError('Field cannot have leading or trialing whitespaces.')
        try:
            email = validate_email(field.data).email
        except EmailNotValidError as e:
            raise ValidationError(f'Invalid email {e}')

    def validate_first_name(self, first_name):
        if not re.match("^[a-zA-Z-]+$", first_name.data):
            raise ValidationError('First name can only contain letters and hyphens.')
        if '  ' in first_name.data:
            raise ValidationError('First name cannot contain consecutive spaces.')

        if not first_name.data.isalpha():
            raise ValidationError('First name can only contain letters.')

    def validate_last_name(self, last_name):
        if not re.match("^[a-zA-Z-]+$", last_name.data):
            raise ValidationError('Last name can only contain letters and hyphens.')

        if '  ' in last_name.data:
            raise ValidationError('Last name cannot contain consecutive spaces.')

        if not last_name.data.isalpha():
            raise ValidationError('Last name can only contain letters.')

    def validate_phone_number(self, phone_number):
        if not re.match("^[0-9]+$", phone_number.data):
            raise ValidationError('Phone number can only contain numbers.')

            # Check for a valid phone number length (adjust as needed)
        min_length = 10
        max_length = 15
        if not min_length <= len(phone_number.data) <= max_length:
            raise ValidationError(f'Phone number must be between {min_length} and {max_length} digits long.')
        # Check for a valid country code

        # valid_country_codes = ['+1', '+44', '+81', '+254', '+255']  # Add more country codes as needed
        # if not any(phone_number.data.startswith(code) for code in valid_country_codes):
        #     raise ValidationError('Invalid country code.')

        # Ensure the phone number doesn't start with a leading zero
        if phone_number.data.startswith('0'):
            raise ValidationError('Phone number cannot start with a leading zero.')

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('That email address is already registered. Please use a different one.')
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email.data):
            raise ValidationError('Invalid email format.')

        allowed_domains = ['example.com', 'gmail.com', 'kabarak.ac.ke']
        if email.data.split('@')[1] not in allowed_domains:
            raise ValidationError('Invalid email domain.')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username is already taken. Please choose a different one.')
        if not username.data[0].isalpha():
            raise ValidationError('Username must start with a letter.')
        if not username.data.isalnum():
            raise ValidationError('Username can only contain letters and numbers.')

    def validate_password(self, password):
        if not any(char.isupper() for char in password.data):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.islower() for char in password.data):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('Password must contain at least one digit.')
        special_characters = "!@#$%^&*()-_+=<>,.?/:;{}[]|"
        if not any(char in special_characters for char in password.data):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*()-_+=<>,.?/:;{}[]|).')
        if self.username.data.lower() in password.data.lower():
            raise ValidationError('Password cannot contain the username.')
        consecutive_char = {''.join(chr(ord(c) + i) for i in range(3)) for c in 'abcdefghijklmnopqrstuvwxyz'} | {
            ''.join(str(i) for i in range(3))}
        if any(consecutive in password.data.lower() for consecutive in consecutive_char):
            raise ValidationError('Password cannot contain consecutive characters (e.g., "abc", "123").')
        if any(password.data.count(char * 2) for char in password.data):
            raise ValidationError('Password cannot contain repeated characters (e.g., "aa", "111").')
        min_length = 8
        if len(password.data) < min_length:
            raise ValidationError(f'Password must be at least {min_length} characters long.')
        max_length = 20
        if len(password.data) > max_length:
            raise ValidationError(f'Password must be at most {max_length} characters long.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)],
                           render_kw={"placeholder": "Username"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=20)],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class AppointmentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()],
                           render_kw={"placeholder": "Username", "class": "form-control"})
    email = StringField('Email', validators=[DataRequired(), Email()],
                        render_kw={"placeholder": "Email", "class": "form-control"})
    title = StringField('Problem Title', validators=[DataRequired(), Length(min=3, max=50)],
                                render_kw={"placeholder": "Title", "class": "form-control"})
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=2, max=1000)],
                                render_kw={"placeholder": "Description", "class": "form-control"})
    location = SelectField('Country', choices=[('Canada', 'Canada'), ('Kenya', 'Kenya'), ('Uganda', 'Uganda')],
                          validators=[DataRequired()],
                          render_kw={"placeholder": "Select Location", "class": "form-control select2_el"})
    date = DateField('Date', validators=[DataRequired()],
                       render_kw={"placeholder": "Date", "class": "form-control"})
    time = TimeField('Time', validators=[DataRequired()],
                       render_kw={"placeholder": "Time", "class": "form-control"})
    submit = SubmitField('Book Now')

# Chatbot form
class ChatBotForm(FlaskForm):
    user_input = StringField('Type here', validators=[DataRequired()],
                             render_kw={"placeholder": "Type here...", "class":"form-control"})
    submit = SubmitField('Send')
