from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.passenger import Passenger
from app.models.booking import Booking
from app.extensions import db
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

passengers_bp = Blueprint('passengers', __name__)


@passengers_bp.get('/me')
@jwt_required()
def get_my_profile():
    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()
    if not passenger:
        return error_response('NOT_FOUND', 'Passenger profile not found.', 404)
    data = passenger.to_dict()
    data['user'] = passenger.user.to_dict() if passenger.user else None
    return success_response(data)


@passengers_bp.put('/me')
@jwt_required()
def update_my_profile():
    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()
    if not passenger:
        return error_response('NOT_FOUND', 'Passenger profile not found.', 404)

    data = request.get_json() or {}
    for field in ['nationality', 'date_of_birth', 'gender', 'address',
                  'emergency_contact_name', 'emergency_contact_phone']:
        if field in data:
            setattr(passenger, field, data[field] or None)

    # Accept both frontend name and DB column name
    expiry = data.get('passport_expiry') or data.get('travel_document_expiry')
    if expiry:
        passenger.travel_document_expiry = expiry

    if data.get('passport_number'):
        passenger.passport_number = data['passport_number']

    db.session.commit()
    return success_response(passenger.to_dict())


@passengers_bp.get('')
@roles_required('admin', 'manager')
def list_passengers():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Passenger.query
    items, total = paginate_query(query, page, per_page)
    result = []
    for p in items:
        d = p.to_dict()
        d['user'] = p.user.to_dict() if p.user else None
        result.append(d)
    return paginated_response(result, page, per_page, total)


@passengers_bp.get('/<int:passenger_id>')
@jwt_required()
def get_passenger(passenger_id):
    passenger = Passenger.query.get_or_404(passenger_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger' and passenger.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    data = passenger.to_dict()
    data['user'] = passenger.user.to_dict() if passenger.user else None
    return success_response(data)


@passengers_bp.put('/<int:passenger_id>')
@jwt_required()
def update_passenger(passenger_id):
    passenger = Passenger.query.get_or_404(passenger_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger' and passenger.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    data = request.get_json() or {}
    updatable = ['nationality', 'date_of_birth', 'gender', 'travel_document_expiry']
    for field in updatable:
        if field in data:
            setattr(passenger, field, data[field])

    if 'passport_number' in data:
        passenger.passport_number = data['passport_number']

    db.session.commit()
    return success_response(passenger.to_dict())


@passengers_bp.get('/<int:passenger_id>/bookings')
@jwt_required()
def passenger_bookings(passenger_id):
    passenger = Passenger.query.get_or_404(passenger_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger' and passenger.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Booking.query.filter_by(passenger_id=passenger_id).order_by(Booking.booked_at.desc())
    items, total = paginate_query(query, page, per_page)
    return paginated_response([b.to_dict() for b in items], page, per_page, total)
