from marshmallow import fields, validate, validates_schema, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.flight import Flight


class FlightSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Flight
        load_instance = True

    flight_number = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    route_id = fields.Int(required=True)
    aircraft_id = fields.Int(required=True)
    departure_datetime = fields.DateTime(required=True)
    arrival_datetime = fields.DateTime(required=True)
    economy_price = fields.Decimal(required=True, validate=validate.Range(min=0))
    business_price = fields.Decimal(validate=validate.Range(min=0), allow_none=True)
    first_class_price = fields.Decimal(validate=validate.Range(min=0), allow_none=True)
    status = fields.Str(validate=validate.OneOf(
        ['scheduled', 'boarding', 'departed', 'arrived', 'delayed', 'cancelled']
    ))
    route = fields.Nested('RouteSchema', dump_only=True)
    aircraft = fields.Nested('AircraftSchema', dump_only=True)

    @validates_schema
    def validate_times(self, data, **kwargs):
        dep = data.get('departure_datetime')
        arr = data.get('arrival_datetime')
        if dep and arr and arr <= dep:
            raise ValidationError('Arrival must be after departure.', 'arrival_datetime')


class FlightListSchema(SQLAlchemyAutoSchema):
    """Lightweight schema for flight search results."""
    class Meta:
        model = Flight
        load_instance = False
        fields = (
            'id', 'flight_number', 'departure_datetime', 'arrival_datetime',
            'departure_gate', 'arrival_gate', 'status', 'economy_price',
            'business_price', 'first_class_price', 'delay_minutes', 'route',
        )

    route = fields.Nested('RouteSchema', dump_only=True)
    economy_price = fields.Decimal()
    business_price = fields.Decimal(allow_none=True)
    first_class_price = fields.Decimal(allow_none=True)
