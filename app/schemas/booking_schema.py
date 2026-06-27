from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.booking import Booking
from app.extensions import ma


class BookingSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Booking
        load_instance = True

    pnr_code = fields.Str(dump_only=True)
    fare_amount = fields.Decimal(dump_only=True)
    status = fields.Str(dump_only=True)
    booked_at = fields.DateTime(dump_only=True)
    cabin_class = fields.Str(required=True, validate=validate.OneOf(['economy', 'business', 'first']))
    flight = fields.Nested('FlightSchema', dump_only=True)
    seat = fields.Nested('SeatSchema', dump_only=True)
    ticket = fields.Nested('TicketSchema', dump_only=True, allow_none=True)


class BookingCreateSchema(ma.Schema):
    flight_id = fields.Int(required=True)
    seat_id = fields.Int(required=True)
    cabin_class = fields.Str(required=True, validate=validate.OneOf(['economy', 'business', 'first']))
    special_requests = fields.Str(allow_none=True)


class TicketSchema(ma.Schema):
    id = fields.Int()
    ticket_number = fields.Str()
    barcode = fields.Str()
    status = fields.Str()
    issued_at = fields.DateTime()
