# chat_bot/calendar_api
import random

from flask import (
    Blueprint, flash, redirect, url_for, render_template, session, sessions, request
)
from flask_login import current_user
import time
from googleapiclient.errors import HttpError
import logging
import os.path
import google.auth
import datetime as dt
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauthlib.oauth2 import OAuth2Error
from chat_bot.models import db

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

SCOPES = ['https://www.googleapis.com/auth/calendar']


def handle_missing_client_secret():
    try:
        raise FileNotFoundError("Client secret file is missing")
    except FileNotFoundError as file_not_found_error:
        logging.error('Client secret file is missing: %s', file_not_found_error)
        flash("Client secret file is missing. Please check your configuration.", 'danger')
        # Redirect to a page with instructions or display a user-friendly message
        return redirect(url_for('instructions_page'))  # Replace 'instructions_page' with the actual route


# def get_google_auth():
#     creds = None
#     try:
#         if os.path.exists("token.json"):
#             creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 creds = run_local_server_flow()
#
#     except FileNotFoundError as file_not_found_error:
#         logging.error("Token file not found: %s", file_not_found_error)
#         flash("Token file not found. Please check your configuration.", 'danger')
#     except google.auth.exceptions.RefreshError as refresh_error:
#         logging.error("Error refreshing credentials: %s", refresh_error)
#         flash("Error refreshing credentials.", 'danger')
#     except Exception as generic_error:
#         logging.error("Error in get_google_auth: %s", generic_error)
#         flash("An unexpected error occurred while fetching Google authentication.")
#
#     return credentials_to_dict(creds) if creds else None

# Existing code
def get_google_auth():
    creds = None
    try:
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = run_local_server_flow()

    except FileNotFoundError as file_not_found_error:
        logging.error("Token file not found: %s", file_not_found_error)
        flash("Token file not found. Please check your configuration.", 'danger')
    except google.auth.exceptions.RefreshError as refresh_error:
        logging.error("Error refreshing credentials: %s", refresh_error)
        flash("Error refreshing credentials.", 'danger')
    except Exception as generic_error:
        logging.error("Error in get_google_auth: %s", generic_error)
        flash("An unexpected error occurred while fetching Google authentication.")

    return credentials_to_dict(creds) if creds else None


# def run_local_server_flow():
#     try:
#         if not os.path.exists("chat_bot/client_secret.json"):
#             raise FileNotFoundError("Client secret file is missing")
#
#         flow = InstalledAppFlow.from_client_secrets_file("chat_bot/client_secret.json", SCOPES)
#         creds = flow.run_local_server(port=0)
#
#         if current_user.is_authenticated:
#             current_user.set_google_calendar_token(creds.to_json())
#
#         with open("token.json", "w") as token_file:
#             token_file.write(creds.to_json())
#
#         return creds
#     except FileNotFoundError as file_not_found_error:
#         logging.error('Client secret file is missing: %s', file_not_found_error)
#         flash("Client secret file is missing. Please check your configuration.", 'danger')
#         raise ValueError("Client secret file is missing")
#
#     except Exception as generic_error:
#         logging.error('Error in run_local_server_flow: %s', generic_error)
#         flash('An unexpected error occurred during the OAuth process.', 'danger')
#         raise ValueError("Error during local server flow")

# Existing code
def run_local_server_flow():
    try:
        if not os.path.exists("chat_bot/client_secret.json"):
            raise FileNotFoundError("Client secret file is missing")

        flow = InstalledAppFlow.from_client_secrets_file("chat_bot/client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)

        if current_user.is_authenticated:
            current_user.set_google_calendar_token(credentials_to_dict(creds))

        with open("token.json", "w") as token_file:
            token_file.write(credentials_to_dict(creds))

        return creds
    except FileNotFoundError as file_not_found_error:
        logging.error('Client secret file is missing: %s', file_not_found_error)
        flash("Client secret file is missing. Please check your configuration.", 'danger')
        raise ValueError("Client secret file is missing")
    except Exception as generic_error:
        logging.error('Error in run_local_server_flow: %s', generic_error)
        flash('An unexpected error occurred during the OAuth process.', 'danger')
        raise ValueError("Error during local server flow")


# def credentials_to_dict(credentials):
#     return {
#         'token': credentials.token,
#         'refresh_token': credentials.refresh_token,
#         'token_uri': credentials.token_uri,
#         'client_id': credentials.client_id,
#         'scopes': credentials.scopes,
#     }
# # Updated code
def credentials_to_dict(credentials):
    return credentials.to_json() if credentials else None


@calendar_bp.route('/oauth2callback')
def oauth2callback():
    try:
        flow_creds = get_google_auth()
        state = session.get('oauth_state')

        if not state:
            return render_template('error.html', message='Invalid OAuth state'), 400

        flow = InstalledAppFlow.from_client_secrets_file(
            'chat_bot/client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            state=state
        )

        try:
            flow.fetch_token(authorization_response=request.url)
            logging.info('OAuth callback successful. Fetching Google Calendar API tokens.')
        except OAuth2Error as oauth_error:
            logging.error(f'OAuth error: {str(oauth_error)}')
            return render_template('auth/error.html', message='OAuth error. Please try again.'), 500
        except Exception as e:
            logging.error(f'Error fetching OAuth tokens: {str(e)}')
            return render_template('auth/error.html', message='Error fetching OAuth tokens'), 500

        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)

        if not flow_creds or not flow_creds.valid:
            handle_token_refresh(flow_creds)

        if not session['credentials']:
            logging.error('No credentials found in the session.')
            return render_template('error.html', message='No credentials found in the session.'), 500

        service = build('calendar', 'v3', credentials=session['credentials'])

    except Exception as e:
        logging.error(f'Error in oauth2callback: {str(e)}')
        return render_template('error.html', message='An error occurred during OAuth callback'), 500

    return redirect(url_for('index'))


def handle_token_refresh(flow_creds):
    if flow_creds and hasattr(flow_creds, 'expired') and flow_creds.expired and hasattr(flow_creds,
                                                                                        'refresh_token') and flow_creds.refresh_token:
        try:
            flow_creds.refresh(Request())
            logging.info('Token refresh successful')
            current_user.set_google_calendar_token(flow_creds.to_json())
            db.session.commit()
        except Exception as generic_error:
            logging.error(f'Token refresh error: {str(generic_error)}')
            return render_template('auth/error.html', message='Error refreshing OAuth tokens'), 500

        with open("token.json", "w") as token:
            token.write(flow_creds.to_json())


def exponential_backoff(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            # Replace the following line with your actual Google Calendar API request
            response = get_google_calendar_service()
            return response
        except HttpError as error:
            if error.resp.status == 403:
                # Exponential backoff: wait 2^retries seconds
                # TODO:  add + random.uniform(0, 1)
                wait_time = 2 ** retries + random.uniform(0, 1)
                time.sleep(wait_time)
                retries += 1
            else:
                raise
    raise Exception("Max retries reached, still receiving 403 error.")


# def get_google_calendar_service():
#     # Define the maximum number of retries
#     max_retries = 5
#     retry_count = 0
#
#     while retry_count < max_retries:
#         try:
#             credentials = get_google_auth()
#             service = build('calendar', 'v3', credentials=credentials)
#             return service
#
#         except google.auth.exceptions.RefreshError as refresh_error:
#             logging.error(f'Token refresh error: {str(refresh_error)}')
#             raise ValueError('Error refreshing Google Calendar API token')
#
#         except google.auth.exceptions.AuthError as auth_error:
#             logging.error(f'Authentication error: {str(auth_error)}')
#             return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401
#
#         except google.auth.exceptions.TransportError as transport_error:
#             logging.error(f'Transport error: {str(transport_error)}')
#             raise ValueError('Error obtaining Google Calendar API service')
#
#         except HttpError as http_error:
#             if http_error.resp.status == 401:
#                 return render_template('auth/login.html', message='Authentication failed. Please log in again.'), 401
#             elif http_error.resp.status == 403 and 'usageLimits' in str(http_error):
#                 # Handle 403 error due to Calendar usage limits exceeded
#                 logging.warning('Calendar usage limits exceeded. Retrying...')
#                 retry_count += 1
#                 sleep_seconds = 2 ** retry_count
#                 time.sleep(sleep_seconds)
#             else:
#                 logging.error(f'Google Calendar API Error: {http_error}')
#                 raise ValueError(f'Google Calendar API Error: {http_error}')
#
#     raise ValueError('Maximum number of retries reached. Unable to obtain Google Calendar API service.')


def get_google_calendar_service():
    # Define the maximum number of retries
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            credentials = get_google_auth()
            service = build('calendar', 'v3', credentials=credentials)
            return service

        except google.auth.exceptions.RefreshError as refresh_error:
            logging.error(f'Token refresh error: {str(refresh_error)}')
            raise ValueError('Error refreshing Google Calendar API token')

        except google.auth.exceptions.AuthError as auth_error:
            logging.error(f'Authentication error: {str(auth_error)}')
            return render_template('error.html', message='Authentication error. Please re-authenticate.'), 401

        except google.auth.exceptions.TransportError as transport_error:
            logging.error(f'Transport error: {str(transport_error)}')
            raise ValueError('Error obtaining Google Calendar API service')

        except HttpError as http_error:
            if http_error.resp.status == 401:
                return render_template('auth/login.html', message='Authentication failed. Please log in again.'), 401
            elif http_error.resp.status == 403 and 'usageLimits' in str(http_error):
                # Handle 403 error due to Calendar usage limits exceeded
                logging.warning('Calendar usage limits exceeded. Retrying...')
                retry_count += 1
                sleep_seconds = 2 ** retry_count
                time.sleep(sleep_seconds)
            else:
                logging.error(f'Google Calendar API Error: {http_error}')
                raise ValueError(f'Google Calendar API Error: {http_error}')

        raise ValueError('Maximum number of retries reached. Unable to obtain Google Calendar API service.')
