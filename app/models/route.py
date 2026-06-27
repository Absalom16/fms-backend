from app.extensions import db


class Route(db.Model):
    __tablename__ = 'routes'
    __table_args__ = (
        db.UniqueConstraint('origin_airport_id', 'destination_airport_id', name='uq_route'),
    )

    id = db.Column(db.Integer, primary_key=True)
    origin_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    destination_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    distance_km = db.Column(db.Integer)
    estimated_duration_minutes = db.Column(db.Integer)

    origin = db.relationship('Airport', back_populates='origin_routes', foreign_keys=[origin_airport_id])
    destination = db.relationship('Airport', back_populates='destination_routes', foreign_keys=[destination_airport_id])
    flights = db.relationship('Flight', back_populates='route')

    def to_dict(self):
        return {
            'id': self.id,
            'origin_airport_id': self.origin_airport_id,
            'destination_airport_id': self.destination_airport_id,
            'distance_km': self.distance_km,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'origin_airport': self.origin.to_dict() if self.origin else None,
            'destination_airport': self.destination.to_dict() if self.destination else None,
        }

    def __repr__(self):
        return f'<Route {self.origin_airport_id} → {self.destination_airport_id}>'
