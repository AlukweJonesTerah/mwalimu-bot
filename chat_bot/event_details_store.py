from datetime import datetime
from chat_bot.models import Appointment
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def store_event_details(user_id, event_id, date, time, title, location, description):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date, '%Y-%m-%d')

    # Check if the event already exists in the database
    existing_event = Appointment.query.filter_by(event_id=event_id).first()

    if existing_event:
        # Update the existing event details if needed
        existing_event.date = date_obj  # Use the datetime object
        existing_event.time = time
        existing_event.title = title
        existing_event.location = location
        existing_event.description = description
        print(f'Existing event: {existing_event}')
    else:
        # Create a new event entry in the database
        new_event = Appointment(
            user_id=user_id,
            event_id=event_id,
            date=date_obj,  # Use the datetime object
            time=time,
            title=title,
            location=location,
            description=description
        )
        print(f"New Events: {new_event}")
        db.session.add(new_event)

    # Commit changes to the database
    db.session.commit()
