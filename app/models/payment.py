from datetime import datetime
from app.extensions import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    payment_method = db.Column(db.Enum('mobile_money', 'card', 'bank_transfer'), nullable=False)
    provider = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.String(20))
    status = db.Column(
        db.Enum('pending', 'completed', 'failed', 'refunded'),
        default='pending',
        nullable=False,
    )
    paid_at = db.Column(db.DateTime)
    refunded_at = db.Column(db.DateTime)
    refund_amount = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', back_populates='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'provider': self.provider,
            'transaction_id': self.transaction_id,
            'phone_number': self.phone_number,
            'status': self.status,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Payment {self.id} {self.status}>'
