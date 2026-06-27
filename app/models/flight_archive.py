from datetime import datetime
from app.extensions import db


class FlightArchive(db.Model):
    __tablename__ = 'flights_archive'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(10), nullable=False)
    route_id = db.Column(db.Integer)
    aircraft_id = db.Column(db.Integer)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    arrival_datetime = db.Column(db.DateTime, nullable=False)
    departure_gate = db.Column(db.String(10))
    arrival_gate = db.Column(db.String(10))
    status = db.Column(
        db.Enum('scheduled', 'boarding', 'departed', 'arrived', 'delayed', 'cancelled'),
        nullable=False,
    )
    economy_price = db.Column(db.Numeric(10, 2), nullable=False)
    business_price = db.Column(db.Numeric(10, 2))
    first_class_price = db.Column(db.Numeric(10, 2))
    delay_minutes = db.Column(db.Integer, default=0)
    delay_reason = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived_by = db.Column(db.Integer)

    @classmethod
    def from_flight(cls, flight, archived_by: int):
        return cls(
            id=flight.id,
            flight_number=flight.flight_number,
            route_id=flight.route_id,
            aircraft_id=flight.aircraft_id,
            departure_datetime=flight.departure_datetime,
            arrival_datetime=flight.arrival_datetime,
            departure_gate=flight.departure_gate,
            arrival_gate=flight.arrival_gate,
            status=flight.status,
            economy_price=flight.economy_price,
            business_price=flight.business_price,
            first_class_price=flight.first_class_price,
            delay_minutes=flight.delay_minutes or 0,
            delay_reason=flight.delay_reason,
            cancellation_reason=flight.cancellation_reason,
            created_by=flight.created_by,
            created_at=flight.created_at,
            updated_at=flight.updated_at,
            archived_by=archived_by,
        )
