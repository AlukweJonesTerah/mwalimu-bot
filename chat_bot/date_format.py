from datetime import datetime
import pytz


def validate_date_and_time(date, time):
    try:
        # Check if date is in the correct format(YYYY-MM-DD)
        datetime.strptime(date, '%Y-%m-%d')

        # Check if time is in  the correct format(HH:MM)
        datetime.strptime(time, '%H:%M')

        return None  # Validate successful, no error message
    except ValueError as e:
        return str(e)


def validate_future_date(date):
    try:
        # Convert the date string to a datetime object
        date_obj = datetime.strptime(date, '%Y-%m-%d')

        # Get the current date
        current_date = datetime.now()

        # Check if the provided date is in the future
        if date_obj > current_date:
            return None  # Validation successful, no error message
        else:
            return 'Appointment date must be in the future'
    except ValueError as e:
        return str(e)  # Return False if there is an issue parsing the date


def convert_to_user_timezone(dt, user_timezone):
    # TODO: obtain the user's timezone from their preferences or profile information.
    utc_dt = dt.replace(tzinfo=pytz.utc)
    user_tz = pytz.timezone(user_timezone)
    user_dt = utc_dt.astimezone(user_tz)
    return user_dt
