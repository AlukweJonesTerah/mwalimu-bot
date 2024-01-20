import logging
from datetime import timezone, datetime

from fastapi import BackgroundTasks
from flask import (
    session, jsonify, render_template, request, Blueprint, current_app
)
from flask_login import login_required, current_user, LoginManager
from celery import Celery
from celery.utils.log import get_task_logger
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import FastAPI, Request
from werkzeug.exceptions import BadRequest

from chat_bot.__init__ import create_app
from chat_bot.config import Config
from chat_bot.date_format import validate_future_date, validate_date_and_time
from chat_bot.logging_configurations import configure_logging
from chat_bot.models import User, Appointment, db
from chat_bot.reminder_send import send_reminder, send_actual_reminder
from chat_bot.forms import AppointmentForm

bp = Blueprint('appointment', __name__, url_prefix='/appointment')
celery = Celery(__name__, broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)
logging.basicConfig(level=logging.INFO)
login_manager = LoginManager()
login_manager.login_view = 'login'

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'
TIME_ZONE = 'UTC'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@celery.task
def sync_with_calendar(user_id, date, time, title, location, description, background_tasks: BackgroundTasks):
    user = User.query.get(user_id)

    if not user:
        return 'User not found'

    google_calendar_token = user.get_google_calendar_token()

    if not google_calendar_token:
        logger.info(f'user_id: {user_id}, google_calendar_token: {google_calendar_token}')
        return 'Google Calendar token not found'

    creds = Credentials.from_authorized_user_info(google_calendar_token, SCOPES)

    try:
        service = build('calendar', 'v3', credentials=creds)
        event_datetime = datetime.strptime(f'{date}T{time}', '%Y-%m-%dT%H:%M')

        event_data = {
            'summary': title,
            'location': location,
            'description': description,
            'colorId': 6,
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'end': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=3'
            ],
            'attendees': [
                {'email': 'tj.papajones@gmail.com'},
                {'email': 'examle@gmail.com'},
                {'email': 'jtalukwe@kabarak.ac.ke'},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()

        event_id = event['id']
        event_datetime_utc = event_datetime.replace(tzinfo=timezone.utc)

        # store_event_details(user_id, event_id, event_datetime_utc, title, location, description)

        reminder_offset_minutes = 10
        reminder_message = send_reminder(user_id, date, time, reminder_offset_minutes, background_tasks)
        background_tasks.add_task(send_actual_reminder, user_id, reminder_message)

        return f'Google Calendar: Appointment scheduled for {event_datetime_utc} was successfully'

    except HttpError as error:
        if error.resp.status == 401:
            return 'Google Calendar API Error: Authentication failed. Please re-authenticate.'
        else:
            logging.error(f'Google Calendar API Error for User {user_id}: {error}')
            return f'Google Calendar API Error for User {user_id}: {error}'
    except Exception as e:
        logging.error(f'Google Calendar API Error for User {user_id}: {str(e)}')
        return f'Google Calendar API Error for User {user_id}: {str(e)}'


@bp.route('/booking', methods=['GET'])
@login_required
def booking():
    appointment_form = AppointmentForm()
    if 'username' in session:
        appointment_form = AppointmentForm()
        return render_template('chatbot/appointment.html', username=session['username'],
                               appointment_form=appointment_form)
    else:
        return render_template('chatbot/appointment.html', appointment_form=appointment_form)


# @bp.post('/schedule_appointment')
# async def schedule_appointment():
#     try:
#         # top code
#         content_type = request.headers.get('Content-Type')
#         if content_type != 'application/json':
#             return jsonify({'error': 'Unsupported Media Type'}), 415
#         form = AppointmentForm(request.form)
#         data = request.get_json()
#
#         if 'user_id' in data and data['user_id'] != current_user.id:
#             return jsonify({'message': 'Unauthorized to modify appointments for other users'}), 403
#         if not form.validate():
#             # Handle validation errors
#             return jsonify({'message': 'Invalid form data'}), 400
#
#         date = data.get('date', '')
#         time = data.get('time', '')
#         title = data.get('title', '')
#         location = data.get('location', '')
#         description = data.get('description', '')
#
#         # Add this line to define reminder_offset_minutes
#         reminder_offset_minutes = data.get('reminder_offset_minutes', 10)  # Set a default value if not provided
#
#         date_error = validate_date_and_time(date, time)
#         if date_error:
#             return jsonify({'message': f'Invalid date or time format. {date_error}'}), 400
#
#         future_date_error = validate_future_date(date)
#         if future_date_error:
#             return jsonify({'message': future_date_error}), 400
#
#         # Handle appointment scheduling logic and database updates
#         calendar_response = sync_with_calendar(current_user.id, date, time, title, location, description,
#                                                background_tasks=BackgroundTasks())
#
#         if 'successfully' in calendar_response.lower():
#             # Insert data into the database (assuming you have a db.session.commit() somewhere)
#             new_appointment = Appointment(user_id=current_user.id, date=date, event_id='event_id_placeholder',
#                                           time=time, title=title, location=location, description=description)
#             db.session.add(new_appointment)
#             db.session.commit()
#
#             # Send a reminder
#             send_reminder(current_user.id, date, time, reminder_offset_minutes, background_tasks=BackgroundTasks())
#
#             return jsonify({'message': 'Appointment scheduled successfully'})
#         else:
#
#             print(f'Displayed time and date: {date}, {time}')
#             return jsonify({'message': f'Failed to schedule appointment: {calendar_response}'}), 500
#
#     except ValueError as value_error:
#         logging.error(f'ValueError during appointment scheduling: {str(value_error)}')
#         return jsonify({'message': f'Internal server error: {str(value_error)}'}), 500
#
#     except BadRequest as bad_request_error:
#         logging.error(f'BadRequest during appointment scheduling: {str(bad_request_error)}')
#         return jsonify({'message': f'Bad request: {str(bad_request_error.description)}'}), 400
#
#     except Exception as e:
#         logging.error(f'Unexpected error during appointment scheduling: {str(e)}')
#         return jsonify({'message': f'Internal server error: {str(e)}'}), 500

# @bp.route('/schedule_appointment', methods=['POST'])
# @login_required
# def schedule_appointment():
#     try:
#         # top code
#         form = AppointmentForm(request.form)
#         data = request.get_json()
#
#         if 'user_id' in data and data['user_id'] != current_user.id:
#             return jsonify({'message': 'Unauthorized to modify appointments for other users'}), 403
#         if not form.validate():
#             # Handle validation errors
#             return jsonify({'message': 'Invalid form data'}), 400
#
#         date = data.get('date', '')
#         time = data.get('time', '')
#         title = data.get('title', '')
#         location = data.get('location', '')
#         description = data.get('description', '')
#
#         # Add this line to define reminder_offset_minutes
#         reminder_offset_minutes = data.get('reminder_offset_minutes', 10)  # Set a default value if not provided
#
#         date_error = validate_date_and_time(date, time)
#         if date_error:
#             return jsonify({'message': f'Invalid date or time format. {date_error}'}), 400
#
#         future_date_error = validate_future_date(date)
#         if future_date_error:
#             return jsonify({'message': future_date_error}), 400
#
#         # Handle appointment scheduling logic and database updates
#         calendar_response = sync_with_calendar(current_user.id, date, time, title, location, description,
#                                                background_tasks=BackgroundTasks())
#
#         if 'successfully' in calendar_response.lower():
#             # Insert data into the database (assuming you have a db.session.commit() somewhere)
#             new_appointment = Appointment(user_id=current_user.id, date=date, event_id='event_id_placeholder',
#                                           time=time, title=title, location=location, description=description)
#             db.session.add(new_appointment)
#             db.session.commit()
#
#             # Send a reminder
#             send_reminder(current_user.id, date, time, reminder_offset_minutes, background_tasks=BackgroundTasks())
#
#             return jsonify({'message': 'Appointment scheduled successfully'})
#         else:
#
#             print(f'Displayed time and date: {date}, {time}')
#             return jsonify({'message': f'Failed to schedule appointment: {calendar_response}'}), 500
#
#     except Exception as e:
#         # Handle unexpected exceptions
#         return jsonify({'message': f'Internal server error: {str(e)}'}), 500

@bp.route('/schedule', methods=['POST'])
@login_required  # Use Flask-Login's login_required decorator for authentication
def schedule_appointment():
    try:
        # top code
        data = request.get_json()

        if 'user_id' in data and data['user_id'] != current_user.id:
            return jsonify({'message': 'Unauthorized to modify appointments for other users'}), 403

        date = data.get('date', '')
        time = data.get('time', '')
        title = data.get('title', '')
        location = data.get('location', '')
        description = data.get('description', '')

        date_error = validate_date_and_time(date, time)
        if date_error:
            return jsonify({'message': f'Invalid date or time format. {date_error}'}), 400

        future_date_error = validate_future_date(date)
        if future_date_error:
            return jsonify({'message': future_date_error}), 400

        # Handle appointment scheduling logic and database updates
        calendar_response = sync_with_calendar(current_user.id, date, time, title, location, description,
                                               background_tasks=BackgroundTasks())

        if 'successfully' in calendar_response.lower():
            # Insert data into the database (assuming you have a db.session.commit() somewhere)
            new_appointment = Appointment(user_id=current_user.id, date=date, event_id='event_id_placeholder',
                                          time=time, title=title, location=location, description=description)
            db.session.add(new_appointment)
            db.session.commit()

            # Send a reminder
            send_reminder(current_user.id, date, time)

            return jsonify({'message': 'Appointment scheduled successfully'})
        else:

            print(f'Displayed time and date: {date}, {time}')
            return jsonify({'message': f'Failed to schedule appointment: {calendar_response}'}), 500

    except Exception as e:
        # Handle unexpected exceptions
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500
