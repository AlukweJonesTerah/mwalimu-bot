from flask import (
    Blueprint, render_template
)
from chat_bot.session_tracker import before_request, heartbeat, leave_site

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route('/')
def index():
    before_request()
    heartbeat()
    leave_site()
    return render_template("chatbot/index.html")
