from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import limiter, db
from app.models.booking import Booking
from app.models.passenger import Passenger
from app.services.booking_service import create_booking, cancel_booking, check_in, confirm_booking
from app.utils.responses import success_response, created_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.get('')
@roles_required('admin', 'manager')
def list_bookings():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Booking.query.order_by(Booking.booked_at.desc())

    status = request.args.get('status')
    if status:
        query = query.filter(Booking.status == status)

    items, total = paginate_query(query, page, per_page)
    return paginated_response([b.to_dict() for b in items], page, per_page, total)


@bookings_bp.post('')
@jwt_required()
def create():
    claims = get_jwt()
    if claims.get('role') != 'passenger':
        return error_response('FORBIDDEN', 'Only passengers can make bookings.', 403)

    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()
    if not passenger:
        return error_response('NO_PROFILE', 'Passenger profile not found.', 404)

    data = request.get_json()
    required = ['flight_id', 'seat_id', 'cabin_class']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    try:
        booking = create_booking(
            passenger=passenger,
            flight_id=data['flight_id'],
            seat_id=data['seat_id'],
            cabin_class=data['cabin_class'],
            special_requests=data.get('special_requests'),
        )
    except ValueError as e:
        return error_response('BOOKING_FAILED', str(e), 409)

    return created_response(booking.to_dict())


@bookings_bp.get('/my')
@jwt_required()
def my_bookings():
    from app.models.flight import Flight
    from app.models.route import Route
    from app.models.airport import Airport
    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()
    if not passenger:
        return error_response('NO_PROFILE', 'Passenger profile not found.', 404)

    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status   = request.args.get('status', '').strip()
    search   = request.args.get('search', '').strip()

    query = Booking.query.filter_by(passenger_id=passenger.id).order_by(Booking.booked_at.desc())

    if status:
        query = query.filter(Booking.status == status)

    if search:
        term = f'%{search}%'
        query = query.join(Booking.flight).join(Flight.route).join(
            Route.origin_airport.of_type(Airport)
        ).filter(
            db.or_(
                Booking.pnr_code.ilike(term),
                Airport.city.ilike(term),
                Airport.iata_code.ilike(term),
            )
        )

    items, total = paginate_query(query, page, per_page)
    return paginated_response([b.to_dict() for b in items], page, per_page, total)


@bookings_bp.get('/<int:booking_id>')
@jwt_required()
def get_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger':
        passenger = Passenger.query.filter_by(user_id=user_id).first()
        if not passenger or booking.passenger_id != passenger.id:
            return error_response('FORBIDDEN', 'Access denied.', 403)

    return success_response(booking.to_dict())


@bookings_bp.get('/pnr/<string:pnr>')
def get_by_pnr(pnr):
    booking = Booking.query.filter_by(pnr_code=pnr.upper()).first_or_404()
    return success_response(booking.to_dict())


@bookings_bp.patch('/<int:booking_id>/cancel')
@jwt_required()
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger':
        passenger = Passenger.query.filter_by(user_id=user_id).first()
        if not passenger or booking.passenger_id != passenger.id:
            return error_response('FORBIDDEN', 'Access denied.', 403)

    data = request.get_json() or {}
    try:
        booking = cancel_booking(booking, reason=data.get('reason'), cancelled_by_user_id=user_id)
    except ValueError as e:
        return error_response('CANCEL_FAILED', str(e), 400)

    return success_response(booking.to_dict())


@bookings_bp.post('/<int:booking_id>/confirm')
@jwt_required()
def confirm(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger':
        passenger = Passenger.query.filter_by(user_id=user_id).first()
        if not passenger or booking.passenger_id != passenger.id:
            return error_response('FORBIDDEN', 'Access denied.', 403)

    try:
        booking = confirm_booking(booking)
    except ValueError as e:
        return error_response('CONFIRM_FAILED', str(e), 400)
    return success_response(booking.to_dict())


@bookings_bp.patch('/<int:booking_id>/check-in')
@jwt_required()
def online_check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()
    if not passenger or booking.passenger_id != passenger.id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    try:
        booking = check_in(booking)
    except ValueError as e:
        return error_response('CHECKIN_FAILED', str(e), 400)

    return success_response(booking.to_dict())
