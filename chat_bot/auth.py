import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, make_response
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user, LoginManager
from chat_bot.forms import RegistrationForm, LoginForm

import logging
import json
from chat_bot.db import get_bd
from chat_bot.models import User, db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from chat_bot.calendar_api import get_google_auth
from chat_bot.field_validation import validate_field_logic

bp = Blueprint('auth', __name__, url_prefix='/auth')
bcrypt = Bcrypt()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_user_email(user=None):
    if isinstance(user, int):
        # If the user is provided as an ID, fetch the user actual instance
        user = User.query.get(user)
    email = getattr(user, 'email', None)
    if email:
        return email
    else:
        logging.warning(f"Failed to retrieve email for user: {user}")
    return None


def handle_google_calendar_token(user):
    try:
        # Obtain the Google Calendar token using your custom function (get_google_auth)
        credentials = get_google_auth()

        if credentials:
            # Print the obtained token
            # obtained_token = credentials.to_json()
            obtained_token = json.dumps(credentials)
            print(f"Obtained Token during registration: {obtained_token}")

            user.set_google_calendar_token(obtained_token)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        logging.error(f'Error saving Google Calendar token: {str(e)}')
        flash(f'Error saving Google Calendar token: {str(e)}', 'danger')

def create_user_from_form(form):
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    return User(
        first_name=form.first_name.data,
        last_name=form.last_name.data,
        phone_number=form.phone_number.data,
        email=form.email.data,
        username=form.username.data,
        password=hashed_password
    )

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            new_user = create_user_from_form(form)
            db.session.add(new_user)
            db.session.commit()

            handle_google_calendar_token(new_user)

            flash('Account was created successfully', 'success')
            return redirect(url_for('auth.login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Error saving user details: {str(e)}')
            flash(f'Error saving user details: {str(e)}', 'danger')
        except IntegrityError as e:
            db.session.rollback()
            logging.error(f'Error saving user details: {str(e)}')
            flash(f'The email or username is already in use. Please choose a different one.', 'danger')
        except Exception as e:
            db.session.rollback()
            logging.error(f'Unexpected error during registration: {str(e)}')
            flash('An unexpected error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html', form=form)


# field validation section
@bp.route('/validation/<field>', methods=['POST'])
def validation_field(field):
    data = request.get_json()
    value_to_validate = data.get(field, '')

    # Perform validation logic here
    validation_result = validate_field_logic(field, value_to_validate)
    return jsonify({'message': validation_result})


@bp.route('/login', methods=['GET'])
def login_page():
    form = LoginForm()
    return render_template('auth/login.html', form=form)


# Updated login route
@bp.route('/login', methods=['POST'])
def login():
    form = LoginForm(request.form)

    try:
        if request.is_json or request.method == 'POST':
            # remember = True if request.form.get('remember') else False
            user = User.query.filter_by(username=form.username.data).first()

            if user and bcrypt.check_password_hash(user.password, form.password.data):
                # login_user(user, remember=remember)
                login_user(user)
                # TODO: to be removed
                session['username'] = form.username.data

                if request.is_json:
                    return jsonify({'message': 'success', 'redirect': url_for('user_input.chatbot')})

                flash(f'Welcome back, {current_user.username}!', 'success')
                logging.info(f'Successful login: {current_user.username}')
                return redirect(url_for('user_input.chatbot'))
            else:
                if request.is_json:
                    return jsonify({'message': 'Invalid username or password'})
                flash('Invalid username or password. Please try again.', 'danger')

        if request.is_json:
            return jsonify({'message': 'Form validation failed'})
        flash('Form validation failed. Please try again.', 'danger')

    except Exception as e:
        if request.is_json:
            return jsonify({'message': 'An error occurred during login'})
        logging.error(f'Error during login: {e}')
        flash(f'An error occurred during login. Please try again. {e}', 'danger')

    return render_template('auth/login.html', form=form)



@bp.errorhandler(404)
def not_found(error):
    resp = make_response(render_template('auth/error.html'))
    resp.headers['X-Something'] = 'A value'
    return resp


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({'message': 'Logout successful', 'redirect': url_for('.login')}), 200
    else:
        flash('You have logged out', 'info')
        return redirect(url_for('.login'))
