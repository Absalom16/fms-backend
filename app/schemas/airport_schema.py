from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.airport import Airport


class AirportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Airport
        load_instance = True

    iata_code = fields.Str(required=True, validate=validate.Length(equal=3))
    icao_code = fields.Str(validate=validate.Length(equal=4), allow_none=True)
    name = fields.Str(required=True)
    city = fields.Str(required=True)
    country = fields.Str(required=True)
    timezone = fields.Str(required=True)
    latitude = fields.Decimal(allow_none=True)
    longitude = fields.Decimal(allow_none=True)
