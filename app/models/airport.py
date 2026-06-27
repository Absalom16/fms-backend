from app.extensions import db


class Airport(db.Model):
    __tablename__ = 'airports'

    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True, nullable=False, index=True)
    icao_code = db.Column(db.String(4), unique=True)
    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Numeric(9, 6))
    longitude = db.Column(db.Numeric(9, 6))

    # Relationships
    origin_routes = db.relationship('Route', back_populates='origin', foreign_keys='Route.origin_airport_id')
    destination_routes = db.relationship('Route', back_populates='destination', foreign_keys='Route.destination_airport_id')

    def to_dict(self):
        return {
            'id': self.id,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'timezone': self.timezone,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
        }

    def __repr__(self):
        return f'<Airport {self.iata_code}>'
