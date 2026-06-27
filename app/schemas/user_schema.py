from marshmallow import fields, validate, validates, ValidationError, pre_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.user import User
from app.extensions import ma


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash',)

    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'passenger', 'crew', 'manager']))
    full_name = fields.Str(dump_only=True)

    @validates('email')
    def validate_email_unique(self, value):
        existing = User.query.filter_by(email=value).first()
        if existing:
            raise ValidationError('Email is already registered.')

    @pre_load
    def lowercase_email(self, data, **kwargs):
        if 'email' in data:
            data['email'] = data['email'].lower().strip()
        return data


class UserPublicSchema(ma.Schema):
    id = fields.Int()
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    full_name = fields.Str()
    phone = fields.Str()
    role = fields.Str()
    is_active = fields.Bool()
    last_login = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
