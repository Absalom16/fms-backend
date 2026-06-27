from datetime import datetime
from app.extensions import db


class Aircraft(db.Model):
    __tablename__ = 'aircraft'

    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100))
    economy_seats = db.Column(db.Integer, nullable=False, default=0)
    business_seats = db.Column(db.Integer, nullable=False, default=0)
    first_class_seats = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Enum('active', 'maintenance', 'retired'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seats = db.relationship('Seat', back_populates='aircraft', cascade='all, delete-orphan')
    flights = db.relationship('Flight', back_populates='aircraft')

    @property
    def total_seats(self):
        return self.economy_seats + self.business_seats + self.first_class_seats

    def to_dict(self):
        return {
            'id': self.id,
            'registration_number': self.registration_number,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'economy_seats': self.economy_seats,
            'business_seats': self.business_seats,
            'first_class_seats': self.first_class_seats,
            'total_seats': self.total_seats,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Aircraft {self.registration_number}>'
