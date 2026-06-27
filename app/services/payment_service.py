import uuid
from datetime import datetime
from app.extensions import db
from app.models.payment import Payment
from app.models.audit_log import AuditLog


def initiate_payment(booking, payment_method, provider=None, phone_number=None, currency='USD'):
    """Create a pending payment record and kick off gateway request."""
    payment = Payment(
        booking_id=booking.id,
        amount=booking.fare_amount,
        currency=currency,
        payment_method=payment_method,
        provider=provider,
        phone_number=phone_number,
        transaction_id=str(uuid.uuid4()),
    )
    db.session.add(payment)
    db.session.commit()

    if payment_method == 'mobile_money':
        _send_mobile_money_push(payment)
    elif payment_method == 'card':
        pass  # Card flow handled client-side via payment gateway SDK

    return payment


def _send_mobile_money_push(payment):
    """Placeholder for mobile money STK push integration."""
    # In production: call MTN/Airtel API to trigger STK push to payment.phone_number
    pass


def handle_webhook(transaction_id, status, gateway_reference=None):
    """Process callback from payment gateway."""
    payment = Payment.query.filter_by(transaction_id=transaction_id).first()
    if not payment:
        return None

    if status == 'success':
        payment.status = 'completed'
        payment.paid_at = datetime.utcnow()
        db.session.commit()

        from app.services.booking_service import confirm_booking
        confirm_booking(payment.booking)

        log = AuditLog(action='PAYMENT', entity_type='payment', entity_id=payment.id,
                       description=f'Payment completed for booking {payment.booking.pnr_code}')
        db.session.add(log)
        db.session.commit()
    elif status == 'failed':
        payment.status = 'failed'
        db.session.commit()

    return payment


def process_refund(booking):
    """Issue a refund for the completed payment on a cancelled booking."""
    completed_payment = Payment.query.filter_by(
        booking_id=booking.id, status='completed'
    ).first()

    if not completed_payment:
        return None

    completed_payment.status = 'refunded'
    completed_payment.refunded_at = datetime.utcnow()
    completed_payment.refund_amount = completed_payment.amount

    log = AuditLog(action='PAYMENT', entity_type='payment', entity_id=completed_payment.id,
                   description=f'Refund issued for booking {booking.pnr_code}')
    db.session.add(log)
    db.session.commit()

    from app.services.notification_service import send_notification
    send_notification(
        user_id=booking.passenger.user_id,
        notif_type='payment_received',
        title='Refund Initiated',
        message=f'A refund of {completed_payment.refund_amount} {completed_payment.currency} '
                f'has been initiated for booking {booking.pnr_code}.',
        send_email=True,
    )
    return completed_payment
