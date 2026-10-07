from ..types.snowflake import Snowflake

from ._convert import EMOJI_MENTION, RAW_ID, require_guild, fail

class Emoji:
    def __init__(self, data:dict):
        id = data.get("id")
        self.id = Snowflake(id)
        self.name = data.get("name")
        self.require_colons = data.get("require_colons", False)
        self.managed = data.get("managed", False)
        self.animated = data.get("animated", False)
        self.available = data.get("available", False)

    @staticmethod
    async def convert(ctx, value:str) -> "Emoji":
        value = value.strip()

        # <:nome:id> ou <a:nome:id> (pode ser de qualquer servidor)
        m = EMOJI_MENTION.match(value)
        if m:
            return Emoji({
                "id": m.group(3),
                "name": m.group(2),
                "animated": bool(m.group(1)),
                "require_colons": True,
                "available": True,
            })

        guild = require_guild(ctx, "Emoji")
        if RAW_ID.match(value):
            for emoji in guild.emojis:
                if str(emoji.id) == value:
                    return emoji
        else:
            name = value.strip(":").lower()
            for emoji in guild.emojis:
                if (emoji.name or "").lower() == name:
                    return emoji

        raise fail("Emoji", value)

    def __int__(self):
        return self.id.value

    def __str__(self):
        return self.name

    def __bool__(self):
        return self.id.value is not None

    def __repr__(self):
        return f"<Emoji id={self.id.value} name={self.name} animated={self.animated}>"
