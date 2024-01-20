# chat_bot/mail_sending.py

import logging
from chat_bot.__init__ import create_app
from celery import shared_task, Celery
from flask import Blueprint
from flask import current_app
from flask_mail import Message, Mail
from email.utils import formataddr
from celery.contrib.abortable import AbortableTask
import smtplib
from email.mime.text import MIMEText
from chat_bot.celery_worker.celery_worker_app import make_celery

mail = Mail()
celery = Celery(__name__)


# mail config
@shared_task(bind=True, base=AbortableTask)
@celery.task
def send_email_with_smtplib(to, subject, body):
    smtp_server = current_app.config['MAIL_SERVER']
    smtp_port = current_app.config['MAIL_PORT']
    smtp_username = current_app.config['MAIL_USERNAME']
    smtp_password = current_app.config['MAIL_PASSWORD']
    sender_email = current_app.config['MAIL_DEFAULT_SENDER']

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = formataddr((f'DigiWave', f'{sender_email}'))
    msg['To'] = to

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, [to], msg.as_string())
        logging.info(f'Email sent using smtplib to {to}')
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f'SMTP Authentication Error: {str(e)}')
    except Exception as e:
        logging.error(f'Failed to send email using smtplib to {to}: {str(e)}', exc_info=True)


@shared_task(bind=True, base=AbortableTask)
@celery.task
def send_email_with_flask_mail(to, subject, body):
    try:
        msg = Message(subject, recipients=[to], body=body)
        mail.send(msg)
        current_app.logger.info(f'Email sent using Flask-Mail to {to} with subject: {subject}')
        return True  # Indicate successful email sending
    except (smtplib.SMTPException, Exception) as e:
        current_app.logger.error(f'Failed to send email using Flask-Mail to {to}: {str(e)}')
        return False  # Indicate failed email sending
