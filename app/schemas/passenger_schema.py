from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.passenger import Passenger


class PassengerSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Passenger
        load_instance = True
        exclude = ('_passport_number',)

    passport_number = fields.Str(load_only=False, allow_none=True)
    date_of_birth = fields.Date(allow_none=True)
    travel_document_expiry = fields.Date(allow_none=True)
    gender = fields.Str(validate=validate.OneOf(['male', 'female', 'other']), allow_none=True)
    frequent_flyer_number = fields.Str(dump_only=True)
    frequent_flyer_points = fields.Int(dump_only=True)
    document_expiring_soon = fields.Bool(dump_only=True)
