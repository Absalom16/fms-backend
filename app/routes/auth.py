import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError
from app.extensions import limiter, db
from app.services.auth_service import register_user, login_user, logout_user, refresh_access_token
from app.models.user import User
from app.utils.responses import success_response, created_response, error_response
from app.utils.helpers import get_client_ip

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/register')
@limiter.limit('10 per minute')
def register():
    data = request.get_json()
    if not data:
        return error_response('INVALID_JSON', 'Request body must be JSON', 400)

    required = ['email', 'password', 'first_name', 'last_name', 'role']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing required fields: {", ".join(missing)}', 422)

    if data['role'] not in ('admin', 'passenger', 'crew', 'manager'):
        return error_response('INVALID_ROLE', 'Invalid role.', 422)

    if len(data.get('password', '')) < 8:
        return error_response('WEAK_PASSWORD', 'Password must be at least 8 characters.', 422)

    existing = User.query.filter_by(email=data['email'].lower().strip()).first()
    if existing:
        return error_response('EMAIL_TAKEN', 'Email is already registered.', 409)

    try:
        user = register_user(data, ip_address=get_client_ip(request))
    except Exception as e:
        return error_response('REGISTRATION_FAILED', str(e), 400)

    from app.services.auth_service import login_user
    _, access_token, refresh_token = login_user(data['email'], data['password'])

    return created_response({
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    })


@auth_bp.post('/login')
@limiter.limit('10 per minute')
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return error_response('MISSING_CREDENTIALS', 'Email and password are required.', 400)

    try:
        user, access_token, refresh_token = login_user(
            data['email'], data['password'], ip_address=get_client_ip(request)
        )
    except ValueError as e:
        return error_response('AUTH_FAILED', str(e), 401)

    return success_response({
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 900,
    })


@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    new_token = refresh_access_token(identity, claims)
    return success_response({'access_token': new_token})


@auth_bp.post('/logout')
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    user_id = int(get_jwt_identity())
    logout_user(jti=jti, user_id=user_id, ip_address=get_client_ip(request))
    return success_response(message='Logged out successfully.')


@auth_bp.post('/forgot-password')
@limiter.limit('5 per minute')
def forgot_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').lower().strip()
    if not email:
        return error_response('MISSING_EMAIL', 'Email is required.', 400)

    user = User.query.filter_by(email=email).first()
    # Always respond with success to avoid email enumeration
    if not user:
        return success_response(message='If that email is registered you will receive a reset link.')

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    reset_url = f'{frontend_url}/reset-password?token={token}'

    # Send email via Flask-Mail
    from app.services.notification_service import _send_email
    _send_email(
        to=user.email,
        subject='SkyWay — Reset your password',
        body=(
            f'Hi {user.first_name},\n\n'
            f'You requested a password reset. Click the link below to choose a new password.\n'
            f'This link expires in 1 hour.\n\n'
            f'{reset_url}\n\n'
            f'If you did not request this, you can safely ignore this email.\n\n'
            f'— The SkyWay Team'
        ),
    )

    current_app.logger.info(f'[PASSWORD RESET] {user.email} → {reset_url}')
    return success_response(message='If that email is registered you will receive a reset link.')


@auth_bp.post('/reset-password')
@limiter.limit('10 per minute')
def reset_password():
    data = request.get_json() or {}
    token    = (data.get('token') or '').strip()
    password = data.get('password') or ''

    if not token or not password:
        return error_response('MISSING_FIELDS', 'Token and new password are required.', 400)

    if len(password) < 8:
        return error_response('WEAK_PASSWORD', 'Password must be at least 8 characters.', 422)

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return error_response('INVALID_TOKEN', 'Reset link is invalid or has already been used.', 400)

    if datetime.utcnow() > user.reset_token_expires:
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return error_response('TOKEN_EXPIRED', 'Reset link has expired. Please request a new one.', 400)

    user.set_password(password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    return success_response(message='Password updated successfully. You can now log in.')


@auth_bp.get('/me')
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = user.to_dict()
    if user.passenger_profile:
        data['passenger_profile'] = user.passenger_profile.to_dict()
    if user.crew_profile:
        data['crew_profile'] = user.crew_profile.to_dict()
    return success_response(data)
