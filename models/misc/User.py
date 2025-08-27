from tortoise import fields, models

from models.helpers import ArrayField


# TODO: make manytomany field in user_data for redeem codes.
class User(models.Model):
    class Meta:
        table = "user_data"

    user_id = fields.BigIntField(pk=True, index=True)
    is_premium = fields.BooleanField(default=False, index=True)  # Premium features are limited by default
    premium_expire_time = fields.DatetimeField(null=True)  # When user's premium expires
    made_premium_by = fields.BigIntField(null=True)  # Owner who granted premium
    premium_granted_at = fields.DatetimeField(null=True)  # When premium was granted
    premium_notified = fields.BooleanField(default=False)  # Notification for premium expiry
    public_profile = fields.BooleanField(default=True)
    # badges = CharVarArrayField(default=list)
    money = fields.IntField(default=0)
