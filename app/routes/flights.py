from datetime import date
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.extensions import limiter
from app.models.flight import Flight
from app.services.flight_service import (
    create_flight, update_flight, update_flight_status,
    search_flights, get_seat_availability,
)
from app.utils.responses import success_response, created_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

flights_bp = Blueprint('flights', __name__)


def _normalise_flight_payload(data: dict) -> None:
    """Map frontend field names to DB column names in-place."""
    if 'base_price' in data and 'economy_price' not in data:
        data['economy_price'] = data.pop('base_price')
    if 'first_price' in data and 'first_class_price' not in data:
        data['first_class_price'] = data.pop('first_price')
    if 'gate' in data and 'departure_gate' not in data:
        data['departure_gate'] = data.pop('gate')


@flights_bp.get('')
@limiter.limit('60 per minute')
def list_flights():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    dep_date_str = request.args.get('departure_date')
    cabin_class = request.args.get('cabin_class')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    if origin and destination and dep_date_str:
        try:
            dep_date = date.fromisoformat(dep_date_str)
        except ValueError:
            return error_response('INVALID_DATE', 'departure_date must be YYYY-MM-DD', 400)
        flights = search_flights(origin, destination, dep_date, cabin_class)
        return paginated_response([f.to_dict() for f in flights], page, per_page, len(flights))

    query = Flight.query.order_by(Flight.departure_datetime)
    status_filter = request.args.get('status')
    search = request.args.get('search', '').strip()
    if status_filter:
        query = query.filter(Flight.status == status_filter)
    if search:
        query = query.filter(Flight.flight_number.ilike(f'%{search}%'))

    items, total = paginate_query(query, page, per_page)
    return paginated_response([f.to_dict() for f in items], page, per_page, total)


@flights_bp.post('')
@roles_required('admin')
def create():
    data = request.get_json()

    # Normalise frontend field names → DB field names
    _normalise_flight_payload(data)

    required = ['flight_number', 'route_id', 'aircraft_id', 'departure_datetime', 'arrival_datetime', 'economy_price']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    from datetime import datetime
    for field in ('departure_datetime', 'arrival_datetime'):
        if isinstance(data.get(field), str):
            data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))

    user_id = int(get_jwt_identity())
    try:
        flight = create_flight(data, created_by=user_id)
    except Exception as e:
        return error_response('CREATE_FAILED', str(e), 400)

    return created_response(flight.to_dict())


@flights_bp.get('/<int:flight_id>')
def get_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    return success_response(flight.to_dict())


@flights_bp.put('/<int:flight_id>')
@roles_required('admin')
def update(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    data = request.get_json()
    _normalise_flight_payload(data)
    from datetime import datetime
    for field in ('departure_datetime', 'arrival_datetime'):
        if isinstance(data.get(field), str):
            data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))

    user_id = int(get_jwt_identity())
    flight = update_flight(flight, data, updated_by=user_id)
    return success_response(flight.to_dict())


@flights_bp.delete('/<int:flight_id>')
@roles_required('admin')
def delete(flight_id):
    from app.extensions import db
    from app.models.flight_archive import FlightArchive
    flight = Flight.query.get_or_404(flight_id)
    user_id = int(get_jwt_identity())
    archive = FlightArchive.from_flight(flight, archived_by=user_id)
    db.session.add(archive)
    db.session.delete(flight)
    db.session.commit()
    return success_response({'id': flight_id, 'archived': True})


@flights_bp.patch('/<int:flight_id>/status')
@roles_required('admin')
def update_status(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    data = request.get_json()
    new_status = data.get('status')
    valid = ('scheduled', 'boarding', 'departed', 'arrived', 'delayed', 'cancelled')
    if not new_status or new_status not in valid:
        return error_response('INVALID_STATUS', f'status must be one of: {", ".join(valid)}', 422)

    user_id = int(get_jwt_identity())
    flight = update_flight_status(
        flight, new_status, updated_by=user_id,
        delay_minutes=data.get('delay_minutes'),
        delay_reason=data.get('delay_reason'),
        cancellation_reason=data.get('cancellation_reason'),
    )
    return success_response(flight.to_dict())


@flights_bp.get('/<int:flight_id>/seats')
def get_seats(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    seats = get_seat_availability(flight)
    return success_response(seats)


@flights_bp.get('/<int:flight_id>/bookings')
@roles_required('admin', 'manager')
def get_flight_bookings(flight_id):
    from app.models.booking import Booking
    Flight.query.get_or_404(flight_id)
    bookings = Booking.query.filter_by(flight_id=flight_id).order_by(Booking.booked_at).all()

    result = []
    for b in bookings:
        d = b.to_dict()
        if b.passenger and b.passenger.user:
            u = b.passenger.user
            d['passenger_name'] = f'{u.first_name} {u.last_name}'
            d['passenger_email'] = u.email
            d['passenger_phone'] = u.phone
        else:
            d['passenger_name'] = 'Unknown'
            d['passenger_email'] = None
            d['passenger_phone'] = None
        result.append(d)

    return success_response(result)


@flights_bp.get('/<int:flight_id>/crew')
@roles_required('admin', 'crew')
def get_flight_crew(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    crew = [a.to_dict() for a in flight.crew_assignments]
    return success_response(crew)
