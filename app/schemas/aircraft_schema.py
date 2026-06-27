from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.aircraft import Aircraft
from app.models.seat import Seat


class AircraftSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Aircraft
        load_instance = True

    registration_number = fields.Str(required=True)
    model = fields.Str(required=True)
    economy_seats = fields.Int(required=True, validate=validate.Range(min=0))
    business_seats = fields.Int(validate=validate.Range(min=0))
    first_class_seats = fields.Int(validate=validate.Range(min=0))
    status = fields.Str(validate=validate.OneOf(['active', 'maintenance', 'retired']))
    total_seats = fields.Int(dump_only=True)


class SeatSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Seat
        load_instance = True

    seat_number = fields.Str(required=True)
    seat_class = fields.Str(required=True, validate=validate.OneOf(['economy', 'business', 'first']))
