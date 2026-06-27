from datetime import datetime
from app.extensions import db


class CrewMember(db.Model):
    __tablename__ = 'crew_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    crew_role = db.Column(db.Enum('pilot', 'co_pilot', 'flight_attendant', 'purser'), nullable=False)
    license_number = db.Column(db.String(50))
    certification_expiry = db.Column(db.Date)
    medical_expiry = db.Column(db.Date)
    hire_date = db.Column(db.Date)
    status = db.Column(db.Enum('active', 'on_leave', 'retired'), default='active', nullable=False)

    user = db.relationship('User', back_populates='crew_profile')
    flight_assignments = db.relationship('FlightCrewAssignment', back_populates='crew_member', lazy='dynamic')

    @property
    def is_certification_valid(self):
        from datetime import date
        if not self.certification_expiry:
            return False
        return self.certification_expiry > date.today()

    @property
    def is_medical_valid(self):
        from datetime import date
        if not self.medical_expiry:
            return False
        return self.medical_expiry > date.today()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'crew_role': self.crew_role,
            'license_number': self.license_number,
            'certification_expiry': self.certification_expiry.isoformat() if self.certification_expiry else None,
            'medical_expiry': self.medical_expiry.isoformat() if self.medical_expiry else None,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'status': self.status,
            'certification_valid': self.is_certification_valid,
            'medical_valid': self.is_medical_valid,
            'user': self.user.to_dict() if self.user else None,
        }

    def __repr__(self):
        return f'<CrewMember {self.employee_id}>'


class FlightCrewAssignment(db.Model):
    __tablename__ = 'flight_crew_assignments'
    __table_args__ = (
        db.UniqueConstraint('flight_id', 'crew_member_id', name='uq_flight_crew'),
    )

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    crew_member_id = db.Column(db.Integer, db.ForeignKey('crew_members.id'), nullable=False)
    role_on_flight = db.Column(db.Enum('captain', 'first_officer', 'purser', 'cabin_crew'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    flight = db.relationship('Flight', back_populates='crew_assignments')
    crew_member = db.relationship('CrewMember', back_populates='flight_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

    def to_dict(self):
        return {
            'id': self.id,
            'flight_id': self.flight_id,
            'crew_member_id': self.crew_member_id,
            'role_on_flight': self.role_on_flight,
            'assigned_at': self.assigned_at.isoformat(),
            'crew_member': self.crew_member.to_dict() if self.crew_member else None,
        }
