from flask import (
    Blueprint, session, jsonify
)
from flask_login import current_user
from datetime import datetime
from chat_bot.models import db

bp = Blueprint('session_tracker', __name__, url_prefix='/session_tracker')


@bp.before_request
def before_request():
    if 'user_id' in session:
        session.permanent = True


@bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401


@bp.route('/leave-site', methods=['POST'])
def leave_site():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401
