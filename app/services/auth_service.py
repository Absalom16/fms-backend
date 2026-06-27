from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti, decode_token
from app.extensions import db
from app.models.user import User
from app.models.passenger import Passenger
from app.models.audit_log import AuditLog


def register_user(data, ip_address=None):
    """Create a new user account and passenger profile if applicable."""
    user = User(
        email=data['email'].lower().strip(),
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        role=data['role'],
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    if data['role'] == 'passenger':
        profile = Passenger(user_id=user.id)
        db.session.add(profile)

    log = AuditLog(user_id=user.id, action='CREATE', entity_type='user', entity_id=user.id,
                   description='User registered', ip_address=ip_address)
    db.session.add(log)
    db.session.commit()
    return user


def login_user(email, password, ip_address=None):
    """Authenticate credentials and return (user, access_token, refresh_token) or raise ValueError."""
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user or not user.check_password(password):
        raise ValueError('Invalid email or password.')
    if not user.is_active:
        raise ValueError('Account is deactivated. Please contact support.')

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    extra_claims = {'role': user.role, 'email': user.email}
    access_token = create_access_token(identity=str(user.id), additional_claims=extra_claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=extra_claims)

    log = AuditLog(user_id=user.id, action='LOGIN', entity_type='user', entity_id=user.id,
                   description='User logged in', ip_address=ip_address)
    db.session.add(log)
    db.session.commit()

    return user, access_token, refresh_token


def logout_user(jti, refresh_jti=None, user_id=None, ip_address=None):
    """Revoke tokens by adding their JTI to the Redis blocklist."""
    import app.extensions as ext
    from flask import current_app

    ttl = int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
    ext.redis_client.setex(f'blocklist:{jti}', ttl, '1')

    if refresh_jti:
        refresh_ttl = int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
        ext.redis_client.setex(f'blocklist:{refresh_jti}', refresh_ttl, '1')

    if user_id:
        log = AuditLog(user_id=user_id, action='LOGOUT', entity_type='user', entity_id=user_id,
                       description='User logged out', ip_address=ip_address)
        db.session.add(log)
        db.session.commit()


def refresh_access_token(identity, claims):
    """Issue a new access token from a valid refresh token."""
    extra_claims = {'role': claims.get('role'), 'email': claims.get('email')}
    return create_access_token(identity=identity, additional_claims=extra_claims)
