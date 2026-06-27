from app.extensions import db, mail
from app.models.notification import Notification
from flask_mail import Message
from flask import current_app


def send_notification(user_id, notif_type, title, message, send_email=False, email_address=None):
    """Persist a notification and optionally dispatch an email."""
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
    )
    db.session.add(notification)
    db.session.commit()

    if send_email:
        _send_email(
            to=email_address or _get_user_email(user_id),
            subject=title,
            body=message,
            notification=notification,
        )

    return notification


def notify_flight_passengers(flight, event):
    """Send notifications to all confirmed passengers on a flight."""
    from app.models.booking import Booking
    from app.models.passenger import Passenger
    from app.models.user import User

    bookings = flight.bookings.filter(
        Booking.status.in_(['confirmed', 'checked_in'])
    ).all()

    type_map = {
        'delayed': ('flight_delayed', 'Flight Delayed',
                    f'Flight {flight.flight_number} is delayed by {flight.delay_minutes} minutes. '
                    f'Reason: {flight.delay_reason or "Under investigation"}'),
        'cancelled': ('flight_cancelled', 'Flight Cancelled',
                      f'Flight {flight.flight_number} has been cancelled. '
                      f'A refund will be processed automatically.'),
        'boarding': ('boarding_reminder', 'Now Boarding',
                     f'Flight {flight.flight_number} is now boarding at gate {flight.departure_gate}.'),
    }

    notif_data = type_map.get(event)
    if not notif_data:
        return

    notif_type, title_tpl, message_tpl = notif_data
    for booking in bookings:
        send_notification(
            user_id=booking.passenger.user_id,
            notif_type=notif_type,
            title=title_tpl,
            message=message_tpl,
            send_email=True,
        )


def _get_user_email(user_id):
    from app.models.user import User
    user = User.query.get(user_id)
    return user.email if user else None


def _send_email(to, subject, body, notification=None):
    if not to:
        return
    try:
        msg = Message(subject=subject, recipients=[to], body=body)
        mail.send(msg)
        if notification:
            notification.email_sent = True
            db.session.commit()
    except Exception as e:
        current_app.logger.error(f'Email send failed to {to}: {e}')
