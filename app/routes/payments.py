from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.passenger import Passenger
from app.services.payment_service import initiate_payment, handle_webhook, process_refund
from app.extensions import limiter
from app.utils.responses import success_response, created_response, error_response
from app.utils.decorators import roles_required

payments_bp = Blueprint('payments', __name__)


@payments_bp.post('')
@jwt_required()
@limiter.limit('20 per minute')
def initiate():
    claims = get_jwt()
    if claims.get('role') != 'passenger':
        return error_response('FORBIDDEN', 'Only passengers can initiate payments.', 403)

    data = request.get_json()
    required = ['booking_id', 'payment_method']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response('MISSING_FIELDS', f'Missing: {", ".join(missing)}', 422)

    booking = Booking.query.get_or_404(data['booking_id'])
    user_id = int(get_jwt_identity())
    passenger = Passenger.query.filter_by(user_id=user_id).first()

    if not passenger or booking.passenger_id != passenger.id:
        return error_response('FORBIDDEN', 'Access denied.', 403)

    if booking.status != 'pending':
        return error_response('INVALID_STATE', f'Booking is already {booking.status}.', 400)

    # Map frontend method names → DB ENUM values, keep provider for tracking
    METHOD_MAP = {
        'mpesa':             ('mobile_money', 'mpesa'),
        'airtel_money':      ('mobile_money', 'airtel'),
        'mtn_mobile_money':  ('mobile_money', 'mtn'),
        'mobile_money':      ('mobile_money', None),
        'credit_card':       ('card', None),
        'card':              ('card', None),
        'bank_transfer':     ('bank_transfer', None),
    }
    raw_method = data.get('payment_method', '')
    db_method, auto_provider = METHOD_MAP.get(raw_method, ('card', None))
    provider = data.get('provider') or auto_provider

    if db_method == 'mobile_money' and not data.get('phone_number'):
        return error_response('MISSING_FIELDS', 'phone_number is required for mobile money.', 422)

    try:
        payment = initiate_payment(
            booking=booking,
            payment_method=db_method,
            provider=provider,
            phone_number=data.get('phone_number'),
            currency=data.get('currency', 'USD'),
        )
    except Exception as e:
        return error_response('PAYMENT_FAILED', str(e), 400)

    response_data = payment.to_dict()
    if db_method == 'mobile_money':
        response_data['message'] = f'Payment request sent to {data.get("phone_number")}. Approve on your phone.'

    return created_response(response_data)


@payments_bp.get('/<int:payment_id>')
@jwt_required()
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get('role') == 'passenger':
        passenger = Passenger.query.filter_by(user_id=user_id).first()
        if not passenger or payment.booking.passenger_id != passenger.id:
            return error_response('FORBIDDEN', 'Access denied.', 403)

    return success_response(payment.to_dict())


@payments_bp.post('/webhook')
def webhook():
    """Receive payment gateway callback — no auth (verified via signature in production)."""
    data = request.get_json()
    if not data:
        return error_response('INVALID_PAYLOAD', 'Expected JSON', 400)

    transaction_id = data.get('transaction_id')
    status = data.get('status')
    if not transaction_id or not status:
        return error_response('MISSING_FIELDS', 'transaction_id and status required', 400)

    payment = handle_webhook(transaction_id, status, data.get('gateway_reference'))
    if not payment:
        return error_response('NOT_FOUND', 'Transaction not found', 404)

    return success_response({'payment_id': payment.id, 'status': payment.status})


@payments_bp.post('/<int:payment_id>/refund')
@roles_required('admin')
def refund(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    if payment.status != 'completed':
        return error_response('INVALID_STATE', 'Only completed payments can be refunded.', 400)

    process_refund(payment.booking)
    return success_response(payment.to_dict())
