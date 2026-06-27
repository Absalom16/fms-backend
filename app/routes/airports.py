from flask import Blueprint, request
from app.models.airport import Airport
from app.models.route import Route
from app.extensions import db
from app.utils.responses import success_response, created_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

airports_bp = Blueprint('airports', __name__)


@airports_bp.get('')
def list_airports():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('q', '')
    query = Airport.query
    if search:
        query = query.filter(
            db.or_(
                Airport.iata_code.ilike(f'%{search}%'),
                Airport.name.ilike(f'%{search}%'),
                Airport.city.ilike(f'%{search}%'),
                Airport.country.ilike(f'%{search}%'),
            )
        )
    items, total = paginate_query(query.order_by(Airport.iata_code), page, per_page)
    return paginated_response([a.to_dict() for a in items], page, per_page, total)


@airports_bp.post('')
@roles_required('admin')
def create():
    data = request.get_json()
    required = ['iata_code', 'name', 'city', 'country', 'timezone']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    existing = Airport.query.filter_by(iata_code=data['iata_code'].upper()).first()
    if existing:
        return error_response('DUPLICATE', 'Airport with this IATA code already exists.', 409)

    airport = Airport(
        iata_code=data['iata_code'].upper(),
        icao_code=data.get('icao_code', '').upper() or None,
        name=data['name'],
        city=data['city'],
        country=data['country'],
        timezone=data['timezone'],
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
    )
    db.session.add(airport)
    db.session.commit()
    return created_response(airport.to_dict())


@airports_bp.get('/<int:airport_id>')
def get_airport(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    return success_response(airport.to_dict())


@airports_bp.get('/routes')
@roles_required('admin')
def list_routes():
    routes = Route.query.all()
    return success_response([r.to_dict() for r in routes])


@airports_bp.post('/routes')
@roles_required('admin')
def create_route():
    data = request.get_json()
    required = ['origin_airport_id', 'destination_airport_id']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    if data['origin_airport_id'] == data['destination_airport_id']:
        return error_response('INVALID_ROUTE', 'Origin and destination must be different.', 422)

    existing = Route.query.filter_by(
        origin_airport_id=data['origin_airport_id'],
        destination_airport_id=data['destination_airport_id'],
    ).first()
    if existing:
        return error_response('DUPLICATE', 'This route already exists.', 409)

    route = Route(
        origin_airport_id=data['origin_airport_id'],
        destination_airport_id=data['destination_airport_id'],
        distance_km=data.get('distance_km'),
        estimated_duration_minutes=data.get('estimated_duration_minutes'),
    )
    db.session.add(route)
    db.session.commit()
    return created_response(route.to_dict())


@airports_bp.get('/routes/<int:route_id>')
@roles_required('admin')
def get_route(route_id):
    route = Route.query.get_or_404(route_id)
    return success_response(route.to_dict())
