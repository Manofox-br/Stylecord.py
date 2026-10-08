from ..types.snowflake import Snowflake

from ._utils.convert import ROLE_MENTION, match_id, require_guild, fail

class Role:
    def __init__(self, data:dict):
        id = data.get("id")
        self.id = Snowflake(id)

        self.name = data.get("name")
        self.description = data.get("description")
        self.permissions = data.get("permissions")
        self.position = data.get("position")
        self.color = data.get("color")
        self.hoist = data.get("hoist", False)
        self.managed = data.get("managed", False)
        self.mentionable = data.get("mentionable", False)
        self.icon = data.get("icon")
        self.unicode_emoji = data.get("unicode_emoji")
        self.flags = data.get("flags", 0)

    @staticmethod
    async def convert(ctx, value:str) -> "Role":
        guild = require_guild(ctx, "Role")
        roles = sorted(guild.roles, key=lambda r: r.position or 0, reverse=True)

        rid = match_id(value, ROLE_MENTION)
        if rid:
            for role in roles:
                if str(role.id) == rid:
                    return role
        else:
            name = value.strip().lstrip("@").lower()
            for role in roles:
                if (role.name or "").lstrip("@").lower() == name:
                    return role

        raise fail("Role", value)

    def __int__(self):
        return self.id.value

    def __str__(self):
        return self.name

    def __bool__(self):
        return self.id.value is not None

    def __repr__(self):
        return f"<Role id={self.id.value} name={self.name} color={self.color}>"
