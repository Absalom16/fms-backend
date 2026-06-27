from datetime import datetime, date
from app.extensions import db
from app.utils.encryption import encrypt_value, decrypt_value
import random
import string


def _generate_ffn():
    prefix = 'FF'
    suffix = ''.join(random.choices(string.digits, k=8))
    return f'{prefix}{suffix}'


class Passenger(db.Model):
    __tablename__ = 'passengers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    _passport_number = db.Column('passport_number', db.String(255))
    nationality = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other'))
    travel_document_expiry = db.Column(db.Date)
    frequent_flyer_number = db.Column(db.String(20), unique=True, default=_generate_ffn)
    frequent_flyer_points = db.Column(db.Integer, default=0, nullable=False)
    address = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='passenger_profile')
    bookings = db.relationship('Booking', back_populates='passenger', lazy='dynamic')

    @property
    def passport_number(self):
        if self._passport_number:
            return decrypt_value(self._passport_number)
        return None

    @passport_number.setter
    def passport_number(self, value):
        self._passport_number = encrypt_value(value) if value else None

    @property
    def is_document_expiring_soon(self):
        if not self.travel_document_expiry:
            return False
        from datetime import timedelta
        return self.travel_document_expiry <= date.today() + timedelta(days=180)

    def to_dict(self):
        expiry = self.travel_document_expiry.isoformat() if self.travel_document_expiry else None
        return {
            'id': self.id,
            'user_id': self.user_id,
            'passport_number': self.passport_number,
            'nationality': self.nationality,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'travel_document_expiry': expiry,
            'passport_expiry': expiry,          # alias for frontend
            'frequent_flyer_number': self.frequent_flyer_number,
            'frequent_flyer_points': self.frequent_flyer_points,
            'loyalty_points': self.frequent_flyer_points,  # alias
            'address': self.address,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'document_expiring_soon': self.is_document_expiring_soon,
        }
