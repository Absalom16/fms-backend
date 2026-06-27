from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.route import Route


class RouteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Route
        load_instance = True

    origin_airport_id = fields.Int(required=True)
    destination_airport_id = fields.Int(required=True)
    origin = fields.Nested('AirportSchema', dump_only=True)
    destination = fields.Nested('AirportSchema', dump_only=True)
