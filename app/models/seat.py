from app.extensions import db


class Seat(db.Model):
    __tablename__ = 'seats'
    __table_args__ = (
        db.UniqueConstraint('aircraft_id', 'seat_number', name='uq_seat_aircraft'),
    )

    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    seat_number = db.Column(db.String(5), nullable=False)
    seat_class = db.Column(db.Enum('economy', 'business', 'first'), nullable=False)
    is_window = db.Column(db.Boolean, default=False)
    is_aisle = db.Column(db.Boolean, default=False)
    is_extra_legroom = db.Column(db.Boolean, default=False)

    aircraft = db.relationship('Aircraft', back_populates='seats')
    bookings = db.relationship('Booking', back_populates='seat')

    def to_dict(self):
        return {
            'id': self.id,
            'aircraft_id': self.aircraft_id,
            'seat_number': self.seat_number,
            'seat_class': self.seat_class,
            'is_window': self.is_window,
            'is_aisle': self.is_aisle,
            'is_extra_legroom': self.is_extra_legroom,
        }

    def __repr__(self):
        return f'<Seat {self.seat_number} ({self.seat_class})>'
