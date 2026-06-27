from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.crew import CrewMember, FlightCrewAssignment


class CrewMemberSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CrewMember
        load_instance = True

    crew_role = fields.Str(required=True, validate=validate.OneOf(['pilot', 'co_pilot', 'flight_attendant', 'purser']))
    status = fields.Str(validate=validate.OneOf(['active', 'on_leave', 'retired']))
    certification_expiry = fields.Date(allow_none=True)
    medical_expiry = fields.Date(allow_none=True)
    hire_date = fields.Date(allow_none=True)
    certification_valid = fields.Bool(dump_only=True)
    medical_valid = fields.Bool(dump_only=True)
    user = fields.Nested('UserPublicSchema', dump_only=True)


class FlightCrewAssignmentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FlightCrewAssignment
        load_instance = True

    role_on_flight = fields.Str(required=True, validate=validate.OneOf(
        ['captain', 'first_officer', 'purser', 'cabin_crew']
    ))
    crew_member = fields.Nested('CrewMemberSchema', dump_only=True)
