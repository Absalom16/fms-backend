from datetime import datetime
from app.extensions import db


class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(10), nullable=False, index=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False, index=True)
    arrival_datetime = db.Column(db.DateTime, nullable=False)
    departure_gate = db.Column(db.String(10))
    arrival_gate = db.Column(db.String(10))
    status = db.Column(
        db.Enum('scheduled', 'boarding', 'departed', 'arrived', 'delayed', 'cancelled'),
        default='scheduled',
        nullable=False,
        index=True,
    )
    economy_price = db.Column(db.Numeric(10, 2), nullable=False)
    business_price = db.Column(db.Numeric(10, 2))
    first_class_price = db.Column(db.Numeric(10, 2))
    delay_minutes = db.Column(db.Integer, default=0)
    delay_reason = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    route = db.relationship('Route', back_populates='flights')
    aircraft = db.relationship('Aircraft', back_populates='flights')
    bookings = db.relationship('Booking', back_populates='flight', lazy='dynamic')
    crew_assignments = db.relationship('FlightCrewAssignment', back_populates='flight', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])

    def price_for_class(self, cabin_class):
        mapping = {
            'economy': self.economy_price,
            'business': self.business_price,
            'first': self.first_class_price,
        }
        return mapping.get(cabin_class)

    def available_seats_count(self, cabin_class=None):
        from .booking import Booking
        booked_query = self.bookings.filter(
            Booking.status.notin_(['cancelled', 'no_show'])
        )
        if cabin_class:
            booked_query = booked_query.filter(Booking.cabin_class == cabin_class)
        return booked_query.count()

    def to_dict(self):
        economy = float(self.economy_price) if self.economy_price else None
        first   = float(self.first_class_price) if self.first_class_price else None
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'route_id': self.route_id,
            'aircraft_id': self.aircraft_id,
            'departure_datetime': self.departure_datetime.isoformat(),
            'arrival_datetime': self.arrival_datetime.isoformat(),
            # canonical names (frontend-aligned)
            'gate': self.departure_gate,
            'terminal': None,
            'base_price': economy,
            'business_price': float(self.business_price) if self.business_price else None,
            'first_price': first,
            # legacy aliases kept for backward compat
            'departure_gate': self.departure_gate,
            'arrival_gate': self.arrival_gate,
            'economy_price': economy,
            'first_class_price': first,
            'status': self.status,
            'delay_minutes': self.delay_minutes,
            'delay_reason': self.delay_reason,
            'cancellation_reason': self.cancellation_reason,
            'route': self.route.to_dict() if self.route else None,
            'aircraft': self.aircraft.to_dict() if self.aircraft else None,
            'created_at': self.created_at.isoformat(),
            'total_seats': self.aircraft.total_seats if self.aircraft else None,
            'booked_seats': self.available_seats_count(),
            'available_seats': (self.aircraft.total_seats - self.available_seats_count()) if self.aircraft else None,
        }

    def __repr__(self):
        return f'<Flight {self.flight_number}>'
