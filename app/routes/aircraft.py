from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.models.aircraft import Aircraft
from app.models.seat import Seat
from app.extensions import db
from app.utils.responses import success_response, created_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

aircraft_bp = Blueprint('aircraft', __name__)


@aircraft_bp.get('')
@roles_required('admin', 'manager')
def list_aircraft():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Aircraft.query
    status = request.args.get('status')
    if status:
        query = query.filter(Aircraft.status == status)
    items, total = paginate_query(query, page, per_page)
    return paginated_response([a.to_dict() for a in items], page, per_page, total)


@aircraft_bp.post('')
@roles_required('admin')
def create():
    data = request.get_json()
    required = ['registration_number', 'model', 'economy_seats']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    existing = Aircraft.query.filter_by(registration_number=data['registration_number']).first()
    if existing:
        return error_response('DUPLICATE', 'Registration number already exists.', 409)

    aircraft = Aircraft(
        registration_number=data['registration_number'],
        model=data['model'],
        manufacturer=data.get('manufacturer'),
        economy_seats=data['economy_seats'],
        business_seats=data.get('business_seats', 0),
        first_class_seats=data.get('first_class_seats', 0),
    )
    db.session.add(aircraft)
    db.session.commit()

    _auto_generate_seats(aircraft)
    return created_response(aircraft.to_dict())


def _auto_generate_seats(aircraft):
    """Generate seat records based on aircraft capacity counts."""
    seats = []
    economy_rows = aircraft.economy_seats // 6
    for row in range(1, economy_rows + 1):
        for col in 'ABCDEF':
            seats.append(Seat(
                aircraft_id=aircraft.id,
                seat_number=f'{row}{col}',
                seat_class='economy',
                is_window=col in ('A', 'F'),
                is_aisle=col in ('C', 'D'),
            ))

    if aircraft.business_seats:
        biz_rows = aircraft.business_seats // 4
        for row in range(economy_rows + 1, economy_rows + biz_rows + 1):
            for col in 'ABCD':
                seats.append(Seat(
                    aircraft_id=aircraft.id,
                    seat_number=f'{row}{col}',
                    seat_class='business',
                    is_window=col in ('A', 'D'),
                    is_aisle=col in ('B', 'C'),
                    is_extra_legroom=True,
                ))

    db.session.bulk_save_objects(seats)
    db.session.commit()


@aircraft_bp.get('/<int:aircraft_id>')
@roles_required('admin', 'manager')
def get_aircraft(aircraft_id):
    aircraft = Aircraft.query.get_or_404(aircraft_id)
    return success_response(aircraft.to_dict())


@aircraft_bp.put('/<int:aircraft_id>')
@roles_required('admin')
def update_aircraft(aircraft_id):
    aircraft = Aircraft.query.get_or_404(aircraft_id)
    data = request.get_json() or {}
    updatable = ['model', 'manufacturer', 'economy_seats', 'business_seats', 'first_class_seats']
    for field in updatable:
        if field in data:
            setattr(aircraft, field, data[field])
    db.session.commit()
    return success_response(aircraft.to_dict())


@aircraft_bp.patch('/<int:aircraft_id>/status')
@roles_required('admin')
def update_status(aircraft_id):
    aircraft = Aircraft.query.get_or_404(aircraft_id)
    data = request.get_json()
    status = data.get('status')
    if status not in ('active', 'maintenance', 'retired'):
        return error_response('INVALID_STATUS', 'status must be active, maintenance, or retired', 422)
    aircraft.status = status
    db.session.commit()
    return success_response(aircraft.to_dict())


@aircraft_bp.get('/<int:aircraft_id>/seats')
@roles_required('admin')
def get_seats(aircraft_id):
    Aircraft.query.get_or_404(aircraft_id)
    seats = Seat.query.filter_by(aircraft_id=aircraft_id).all()
    return success_response([s.to_dict() for s in seats])
