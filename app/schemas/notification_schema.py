from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.notification import Notification


class NotificationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Notification
        load_instance = True

    is_read = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
