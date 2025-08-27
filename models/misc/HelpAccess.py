from tortoise import fields
from models import BaseDbModel

class HelpAccess(BaseDbModel):
    class Meta:
        table = "help_access"

    user_id = fields.BigIntField(pk=True, index=True)
    granted_by = fields.BigIntField(null=True)  # Owner who granted access
    granted_at = fields.DatetimeField(auto_now_add=True)
    guild_id = fields.BigIntField(null=True)  # If access is guild-specific
