from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from .responses import error_response
from .helpers import get_client_ip


def roles_required(*roles):
    """Restrict endpoint to users with the given role(s)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') not in roles:
                return error_response('FORBIDDEN', 'You do not have permission to perform this action', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def audit_action(action, entity_type, get_entity_id=None):
    """Log an audit entry after the decorated route handler runs successfully."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)
            try:
                from app.extensions import db
                from app.models.audit_log import AuditLog
                user_id = None
                try:
                    user_id = int(get_jwt_identity())
                except Exception:
                    pass

                entity_id = None
                if get_entity_id:
                    entity_id = get_entity_id(kwargs)

                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    description=f'{action} on {entity_type}',
                    ip_address=get_client_ip(request),
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                pass
            return response
        return wrapper
    return decorator
