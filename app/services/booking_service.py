from datetime import datetime, timedelta
from app.extensions import db
from app.models.booking import Booking
from app.models.flight import Flight
from app.models.seat import Seat
from app.models.ticket import Ticket
from app.models.passenger import Passenger
from app.models.audit_log import AuditLog
from app.services.notification_service import send_notification


def create_booking(passenger, flight_id, seat_id, cabin_class, special_requests=None):
    flight = Flight.query.get_or_404(flight_id)
    seat = Seat.query.get_or_404(seat_id)

    if flight.status in ('cancelled', 'departed', 'arrived'):
        raise ValueError(f'Bookings are not available for flights with status: {flight.status}')

    if seat.aircraft_id != flight.aircraft_id:
        raise ValueError('Seat does not belong to the aircraft operating this flight.')

    existing = Booking.query.filter_by(
        flight_id=flight_id, seat_id=seat_id
    ).filter(Booking.status.notin_(['cancelled', 'no_show'])).first()
    if existing:
        raise ValueError('This seat is already booked for this flight.')

    fare = flight.price_for_class(cabin_class)
    if fare is None:
        raise ValueError(f'No pricing available for {cabin_class} class on this flight.')

    booking = Booking(
        passenger_id=passenger.id,
        flight_id=flight_id,
        seat_id=seat_id,
        cabin_class=cabin_class,
        fare_amount=fare,
        special_requests=special_requests,
    )
    db.session.add(booking)
    db.session.commit()

    log = AuditLog(user_id=passenger.user_id, action='CREATE', entity_type='booking',
                   entity_id=booking.id, description=f'Booking {booking.pnr_code} created')
    db.session.add(log)
    db.session.commit()
    return booking


def confirm_booking(booking):
    """Confirm booking and issue a ticket after successful payment."""
    from datetime import datetime, timezone
    from app.models.payment import Payment

    booking.status = 'confirmed'
    ticket = Ticket(booking_id=booking.id)
    db.session.add(ticket)

    # Mark the most recent pending payment as completed so revenue reports reflect it
    pending_payment = Payment.query.filter_by(
        booking_id=booking.id, status='pending'
    ).order_by(Payment.created_at.desc()).first()
    if pending_payment:
        pending_payment.status = 'completed'
        pending_payment.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.session.commit()

    # Award frequent flyer points (1 point per dollar)
    passenger = booking.passenger
    passenger.frequent_flyer_points += int(booking.fare_amount)
    db.session.commit()

    send_notification(
        user_id=passenger.user_id,
        notif_type='booking_confirmed',
        title='Booking Confirmed',
        message=f'Your booking {booking.pnr_code} for flight {booking.flight.flight_number} is confirmed.',
        send_email=True,
    )
    return booking


def cancel_booking(booking, reason=None, cancelled_by_user_id=None):
    if booking.status in ('cancelled', 'boarded', 'no_show'):
        raise ValueError(f'Cannot cancel a booking with status: {booking.status}')

    booking.status = 'cancelled'
    booking.cancelled_at = datetime.utcnow()
    booking.cancellation_reason = reason

    if booking.ticket:
        booking.ticket.status = 'cancelled'

    log = AuditLog(user_id=cancelled_by_user_id, action='DELETE', entity_type='booking',
                   entity_id=booking.id, description=f'Booking {booking.pnr_code} cancelled')
    db.session.add(log)
    db.session.commit()

    send_notification(
        user_id=booking.passenger.user_id,
        notif_type='flight_cancelled',
        title='Booking Cancelled',
        message=f'Your booking {booking.pnr_code} has been cancelled.',
        send_email=True,
    )
    return booking


def check_in(booking):
    if booking.status != 'confirmed':
        raise ValueError('Only confirmed bookings can be checked in.')

    flight = booking.flight
    now = datetime.utcnow()
    check_in_open = flight.departure_datetime - timedelta(hours=24)
    check_in_close = flight.departure_datetime - timedelta(minutes=45)

    if now < check_in_open:
        raise ValueError('Online check-in is not open yet (opens 24h before departure).')
    if now > check_in_close:
        raise ValueError('Online check-in has closed (closes 45 minutes before departure).')

    booking.status = 'checked_in'
    booking.checked_in_at = now
    db.session.commit()
    return booking
