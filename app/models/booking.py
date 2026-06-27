from datetime import datetime
from app.extensions import db
from app.utils.helpers import generate_pnr


class Booking(db.Model):
    __tablename__ = 'bookings'
    __table_args__ = (
        db.UniqueConstraint('flight_id', 'seat_id', name='uq_booking_seat'),
    )

    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    pnr_code = db.Column(db.String(6), unique=True, nullable=False, default=generate_pnr, index=True)
    cabin_class = db.Column(db.Enum('economy', 'business', 'first'), nullable=False)
    fare_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum('pending', 'confirmed', 'cancelled', 'checked_in', 'boarded', 'no_show'),
        default='pending',
        nullable=False,
    )
    special_requests = db.Column(db.Text)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    checked_in_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)

    passenger = db.relationship('Passenger', back_populates='bookings')
    flight = db.relationship('Flight', back_populates='bookings')
    seat = db.relationship('Seat', back_populates='bookings')
    ticket = db.relationship('Ticket', back_populates='booking', uselist=False, cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='booking', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'passenger_id': self.passenger_id,
            'flight_id': self.flight_id,
            'seat_id': self.seat_id,
            'pnr_code': self.pnr_code,
            'cabin_class': self.cabin_class,
            'fare_amount': float(self.fare_amount),
            'status': self.status,
            'special_requests': self.special_requests,
            'booked_at': self.booked_at.isoformat(),
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'flight': self.flight.to_dict() if self.flight else None,
            'seat': self.seat.to_dict() if self.seat else None,
            'ticket': self.ticket.to_dict() if self.ticket else None,
        }

    def __repr__(self):
        return f'<Booking {self.pnr_code}>'
