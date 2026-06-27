from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification import Notification
from app.extensions import db
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.helpers import paginate_query

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.get('')
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc())
    items, total = paginate_query(query, page, per_page)
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    from flask import jsonify
    import math
    return jsonify({
        'success': True,
        'data': [n.to_dict() for n in items],
        'unread_count': unread_count,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': math.ceil(total / per_page) if per_page else 1,
        },
    }), 200


@notifications_bp.patch('/<int:notification_id>/read')
@jwt_required()
def mark_read(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user_id:
        return error_response('FORBIDDEN', 'Access denied.', 403)
    notification.is_read = True
    db.session.commit()
    return success_response(notification.to_dict())


@notifications_bp.patch('/read-all')
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return success_response(message='All notifications marked as read.')
