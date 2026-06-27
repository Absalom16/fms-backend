from datetime import datetime
from app.extensions import db
from app.utils.helpers import generate_ticket_number, generate_barcode


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), unique=True, nullable=False)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_ticket_number)
    barcode = db.Column(db.String(100), unique=True, nullable=False, default=generate_barcode)
    status = db.Column(db.Enum('active', 'used', 'cancelled'), default='active', nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', back_populates='ticket')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'ticket_number': self.ticket_number,
            'barcode': self.barcode,
            'status': self.status,
            'issued_at': self.issued_at.isoformat(),
        }

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'
