import datetime as dt
import logging
import smtplib
from datetime import datetime

from celery import Celery
from celery.utils.log import get_task_logger
from fastapi import BackgroundTasks

from chat_bot.auth import get_user_email
from chat_bot.mail_sending import send_email_with_flask_mail, send_email_with_smtplib

celery = Celery(__name__, broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)


@celery.task()
def send_reminder(user_id, date, time, reminder_offset_minutes, background_tasks: BackgroundTasks):
    # Set the reminder time, ... 30 minutes before the appointment
    reminder_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M') - dt.timedelta(
        minutes=reminder_offset_minutes)

    # Check if it's time to send the reminder
    current_datetime = datetime.utcnow()
    if current_datetime >= reminder_datetime:
        # It's time to send the reminder
        reminder_message = f"Reminder: Your appointment is scheduled for {date} at {time}. Don't forget!"

        # Schedule the actual sending of the reminder in the background
        background_tasks.add_task(send_actual_reminder, user_id, reminder_message)
        return reminder_message
    else:
        # Reminder is not due yet
        logging.info(f"Reminder schedule for {reminder_datetime}")
        return f"Reminder schedule for {reminder_datetime}"


@celery.task
def send_actual_reminder(user_id, reminder_message):
    try:
        logger.info(f'Sending reminder to user {user_id} with subject: {reminder_message}')
        print(f"Sending reminder to user {user_id}: {reminder_message}")

        # TODO: add user email to database (user_email)
        # temporary_email = 'terahjones@gmail.com'
        email = get_user_email(user_id)

        # Call the appropriate email-sending function asynchronously
        send_email_with_flask_mail.apply_async(args=[email, "Reminder", reminder_message])
        # ro:
        send_email_with_smtplib.apply_async(args=[email, "Reminder", reminder_message])
    except (smtplib.SMTPException, Exception) as e:
        logger.error(f'Failed to send reminder to user {user_id}: {str(e)}')
