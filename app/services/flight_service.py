from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import aliased
from app.extensions import db
from app.models.flight import Flight
from app.models.route import Route
from app.models.airport import Airport
from app.models.aircraft import Aircraft
from app.models.seat import Seat
from app.models.booking import Booking
from app.models.audit_log import AuditLog
from app.services.notification_service import notify_flight_passengers


def create_flight(data, created_by):
    flight = Flight(
        flight_number=data['flight_number'],
        route_id=data['route_id'],
        aircraft_id=data['aircraft_id'],
        departure_datetime=data['departure_datetime'],
        arrival_datetime=data['arrival_datetime'],
        departure_gate=data.get('departure_gate'),
        arrival_gate=data.get('arrival_gate'),
        economy_price=data['economy_price'],
        business_price=data.get('business_price'),
        first_class_price=data.get('first_class_price'),
        created_by=created_by,
    )
    db.session.add(flight)
    db.session.commit()

    log = AuditLog(user_id=created_by, action='CREATE', entity_type='flight', entity_id=flight.id,
                   description=f'Created flight {flight.flight_number}')
    db.session.add(log)
    db.session.commit()
    return flight


def update_flight(flight, data, updated_by):
    updatable = [
        'flight_number', 'route_id', 'aircraft_id', 'status',
        'departure_datetime', 'arrival_datetime',
        'departure_gate', 'arrival_gate',
        'economy_price', 'business_price', 'first_class_price',
    ]
    for field in updatable:
        if field in data:
            setattr(flight, field, data[field])

    log = AuditLog(user_id=updated_by, action='UPDATE', entity_type='flight', entity_id=flight.id,
                   description=f'Updated flight {flight.flight_number}')
    db.session.add(log)
    db.session.commit()
    return flight


def update_flight_status(flight, status, updated_by, delay_minutes=None, delay_reason=None, cancellation_reason=None):
    old_status = flight.status
    flight.status = status

    if status == 'delayed':
        flight.delay_minutes = delay_minutes or 0
        flight.delay_reason = delay_reason

    if status == 'cancelled':
        flight.cancellation_reason = cancellation_reason
        _cancel_all_bookings(flight, updated_by)

    log = AuditLog(user_id=updated_by, action='UPDATE', entity_type='flight', entity_id=flight.id,
                   description=f'Status changed {old_status} → {status}')
    db.session.add(log)
    db.session.commit()

    if status in ('delayed', 'cancelled', 'boarding'):
        notify_flight_passengers(flight, status)

    return flight


def _cancel_all_bookings(flight, cancelled_by):
    """Cancel all non-cancelled bookings on a cancelled flight and trigger refunds."""
    from app.services.payment_service import process_refund

    bookings = flight.bookings.filter(
        Booking.status.notin_(['cancelled', 'no_show'])
    ).all()

    for booking in bookings:
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = 'Flight cancelled by airline'
        process_refund(booking)

    db.session.commit()


def search_flights(origin, destination, departure_date, cabin_class=None):
    OriginAirport = aliased(Airport, name='origin_airport')
    DestinationAirport = aliased(Airport, name='dest_airport')

    query = db.session.query(Flight).join(
        Route, Flight.route_id == Route.id
    ).join(
        OriginAirport, Route.origin_airport_id == OriginAirport.id
    ).join(
        DestinationAirport, Route.destination_airport_id == DestinationAirport.id
    ).filter(
        OriginAirport.iata_code == origin.upper(),
        DestinationAirport.iata_code == destination.upper(),
        func.date(Flight.departure_datetime) == departure_date,
        Flight.status.in_(['scheduled', 'delayed']),
    )

    if cabin_class == 'business':
        query = query.filter(Flight.business_price.isnot(None))
    elif cabin_class == 'first':
        query = query.filter(Flight.first_class_price.isnot(None))

    return query.order_by(Flight.departure_datetime).all()


def get_seat_availability(flight):
    """Return all seats for this flight's aircraft with availability status."""
    booked_seat_ids = db.session.query(Booking.seat_id).filter(
        Booking.flight_id == flight.id,
        Booking.status.notin_(['cancelled', 'no_show']),
    ).subquery()

    seats = Seat.query.filter_by(aircraft_id=flight.aircraft_id).all()
    result = []
    for seat in seats:
        seat_dict = seat.to_dict()
        seat_dict['is_available'] = seat.id not in [s[0] for s in db.session.query(booked_seat_ids).all()]
        result.append(seat_dict)
    return result
