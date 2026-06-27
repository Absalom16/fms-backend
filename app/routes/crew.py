from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.crew import CrewMember, FlightCrewAssignment
from app.models.flight import Flight
from app.services.crew_service import create_crew_member, assign_crew_to_flight, remove_crew_from_flight
from app.extensions import db
from app.utils.responses import success_response, created_response, error_response, paginated_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query

crew_bp = Blueprint('crew', __name__)


@crew_bp.get('/me')
@jwt_required()
def my_profile():
    from datetime import datetime
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    if claims.get('role') != 'crew':
        return error_response('FORBIDDEN', 'Access denied.', 403)

    crew = CrewMember.query.filter_by(user_id=user_id).first_or_404()

    assignments = (
        FlightCrewAssignment.query
        .filter_by(crew_member_id=crew.id)
        .join(Flight, FlightCrewAssignment.flight_id == Flight.id)
        .order_by(Flight.departure_datetime)
        .all()
    )

    def assignment_dict(a):
        d = {
            'id': a.id,
            'flight_id': a.flight_id,
            'role_on_flight': a.role_on_flight,
            'assigned_at': a.assigned_at.isoformat(),
        }
        if a.flight:
            d['flight'] = a.flight.to_dict()
        return d

    result = crew.to_dict()
    result['assignments'] = [assignment_dict(a) for a in assignments]
    return success_response(result)


@crew_bp.get('')
@roles_required('admin', 'manager')
def list_crew():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = CrewMember.query
    role_filter = request.args.get('role')
    if role_filter:
        query = query.filter(CrewMember.crew_role == role_filter)
    items, total = paginate_query(query, page, per_page)
    return paginated_response([c.to_dict() for c in items], page, per_page, total)


@crew_bp.post('')
@roles_required('admin')
def create():
    data = request.get_json()
    required = ['user_id', 'employee_id', 'crew_role']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    try:
        crew = create_crew_member(data)
    except Exception as e:
        return error_response('CREATE_FAILED', str(e), 400)

    return created_response(crew.to_dict())


@crew_bp.get('/<int:crew_id>')
@jwt_required()
def get_crew(crew_id):
    crew = CrewMember.query.get_or_404(crew_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'crew' and crew.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    return success_response(crew.to_dict())


@crew_bp.put('/<int:crew_id>')
@roles_required('admin')
def update_crew(crew_id):
    crew = CrewMember.query.get_or_404(crew_id)
    data = request.get_json() or {}
    updatable = ['license_number', 'certification_expiry', 'medical_expiry', 'status', 'crew_role']
    for field in updatable:
        if field in data:
            setattr(crew, field, data[field])
    db.session.commit()
    return success_response(crew.to_dict())


@crew_bp.get('/<int:crew_id>/flights')
@jwt_required()
def crew_flights(crew_id):
    crew = CrewMember.query.get_or_404(crew_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'crew' and crew.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    assignments = crew.flight_assignments.all()
    return success_response([a.to_dict() for a in assignments])


@crew_bp.post('/flights/<int:flight_id>/crew')
@roles_required('admin')
def assign_to_flight(flight_id):
    data = request.get_json()
    required = ['crew_member_id', 'role_on_flight']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    user_id = int(get_jwt_identity())
    try:
        assignment = assign_crew_to_flight(
            flight_id=flight_id,
            crew_member_id=data['crew_member_id'],
            role_on_flight=data['role_on_flight'],
            assigned_by=user_id,
        )
    except ValueError as e:
        return error_response('ASSIGNMENT_FAILED', str(e), 409)

    return created_response(assignment.to_dict())


@crew_bp.delete('/flights/<int:flight_id>/crew/<int:crew_member_id>')
@roles_required('admin')
def remove_from_flight(flight_id, crew_member_id):
    user_id = int(get_jwt_identity())
    try:
        remove_crew_from_flight(flight_id, crew_member_id, removed_by=user_id)
    except Exception as e:
        return error_response('REMOVE_FAILED', str(e), 400)
    return success_response(message='Crew member removed from flight.')
