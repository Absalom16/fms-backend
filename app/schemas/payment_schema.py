from marshmallow import fields, validate, validates_schema, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.payment import Payment
from app.extensions import ma


class PaymentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True

    amount = fields.Decimal(dump_only=True)
    status = fields.Str(dump_only=True)
    transaction_id = fields.Str(dump_only=True)
    paid_at = fields.DateTime(dump_only=True, allow_none=True)


class PaymentCreateSchema(ma.Schema):
    booking_id = fields.Int(required=True)
    payment_method = fields.Str(required=True, validate=validate.OneOf(['mobile_money', 'card', 'bank_transfer']))
    provider = fields.Str(allow_none=True)
    phone_number = fields.Str(allow_none=True)
    currency = fields.Str(missing='USD', validate=validate.Length(equal=3))

    @validates_schema
    def validate_mobile_money_fields(self, data, **kwargs):
        if data.get('payment_method') == 'mobile_money' and not data.get('phone_number'):
            raise ValidationError('phone_number is required for mobile money payments.', 'phone_number')
