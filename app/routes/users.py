from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models.user import User
from app.utils.responses import success_response, error_response, paginated_response, created_response
from app.utils.decorators import roles_required
from app.utils.helpers import paginate_query, get_client_ip

users_bp = Blueprint('users', __name__)


@users_bp.post('')
@roles_required('admin')
def create_user():
    data = request.get_json() or {}
    required = ['email', 'password', 'first_name', 'last_name', 'role']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    if data['role'] not in ('admin', 'manager', 'crew'):
        return error_response('INVALID_ROLE', 'Role must be admin, manager, or crew.', 422)

    if len(data.get('password', '')) < 8:
        return error_response('WEAK_PASSWORD', 'Password must be at least 8 characters.', 422)

    # Crew-specific validation
    if data['role'] == 'crew':
        crew_required = ['crew_role', 'employee_id']
        missing_crew = [f for f in crew_required if not data.get(f)]
        if missing_crew:
            return error_response('MISSING_FIELDS', f'Missing crew fields: {", ".join(missing_crew)}', 422)
        valid_crew_roles = ('pilot', 'co_pilot', 'flight_attendant', 'purser')
        if data['crew_role'] not in valid_crew_roles:
            return error_response('INVALID_CREW_ROLE', f'crew_role must be one of: {", ".join(valid_crew_roles)}', 422)
        from app.models.crew import CrewMember as CM
        if CM.query.filter_by(employee_id=data['employee_id']).first():
            return error_response('EMPLOYEE_ID_TAKEN', 'Employee ID is already in use.', 409)

    existing = User.query.filter_by(email=data['email'].lower().strip()).first()
    if existing:
        return error_response('EMAIL_TAKEN', 'Email is already registered.', 409)

    from app.services.auth_service import register_user
    user = register_user(data, ip_address=get_client_ip(request))

    # Create crew member profile
    if data['role'] == 'crew':
        from app.services.crew_service import create_crew_member
        create_crew_member({
            'user_id': user.id,
            'employee_id': data['employee_id'],
            'crew_role': data['crew_role'],
        })

    return created_response(user.to_dict())


@users_bp.get('')
@roles_required('admin')
def list_users():
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search   = request.args.get('search', '').strip()
    role     = request.args.get('role', '').strip()
    status   = request.args.get('status', '').strip()

    query = User.query.order_by(User.created_at.desc())
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if role:
        query = query.filter(User.role == role)
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)

    items, total = paginate_query(query, page, per_page)
    return paginated_response([u.to_dict() for u in items], page, per_page, total)


@users_bp.patch('/<int:user_id>/activate')
@roles_required('admin')
def activate(user_id):
    current_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user_id == current_id:
        return error_response('FORBIDDEN', 'Cannot change your own account status.', 403)
    user.is_active = True
    db.session.commit()
    return success_response(user.to_dict())


@users_bp.patch('/<int:user_id>/deactivate')
@roles_required('admin')
def deactivate(user_id):
    current_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user_id == current_id:
        return error_response('FORBIDDEN', 'Cannot change your own account status.', 403)
    user.is_active = False
    db.session.commit()
    return success_response(user.to_dict())
