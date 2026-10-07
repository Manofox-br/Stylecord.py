from .._utils import restapi

from ..types.snowflake import Snowflake
from ._convert import USER_MENTION, match_id, find_user_data, find_member_data, search_member_data, fail

from .assets import Asset, UserAssets

class _LazyDM:
    def __init__(self, user):
        self._user = user

    def __await__(self):
        return self._user.create_dm().__await__()

    async def send(self, content:str, tts:bool = False):
        return await self._user.send(content, tts=tts)

class User:
    def __init__(self, data:dict):
        # Identificação
        id = data.get("id") or data.get("user_id")
        self.id = Snowflake(id)
        self.name = data.get("username")
        self.global_name = data.get("global_name")
        self.discriminator = data.get("discriminator")
        self.bot = data.get("bot", False)

        # Aparência
        avatar_hash = data.get("avatar")
        banner_hash = data.get("banner")
        avatar_decoration_data = data.get("avatar_decoration_data")
        
        if avatar_hash:
            ext = "gif" if avatar_hash.startswith("a_") else "png"
            self.avatar = Asset(f"avatars/{id}/{avatar_hash}.{ext}")
        else:
            self.avatar = Asset(None)

        self.banner = Asset(f"banners/{id}/{banner_hash}.png") if banner_hash else Asset(None)

        if avatar_decoration_data and avatar_decoration_data.get("asset"):
            self.avatar_decoration = Asset(
                f"avatar-decorations/{id}/{avatar_decoration_data['asset']}.png"
            )
        else:
            self.avatar_decoration = Asset(None)
        
        self.user_assets = UserAssets(
            user_id=self.id,
            avatar_hash=avatar_hash,
            banner_hash=banner_hash,
            avatar_decoration_data=avatar_decoration_data
        )
        self.display_name_styles = data.get("display_name_styles")
        self.vad_colors = data.get("vad_colors")
        
        # Flags e extras
        self.public_flags = data.get("public_flags", 0)
        self.primary_guild = data.get("primary_guild")
        self.clan = data.get("clan")

        # Colecionáveis (ex.: nameplate)
        self.collectibles = data.get("collectibles", {})

    @staticmethod
    async def convert(ctx, value:str) -> "User":
        if match_id(value, USER_MENTION):
            return User(await find_user_data(ctx, value))

        # Nome (sem menção/ID): tenta achar um membro do servidor com esse nome exato.
        data = await search_member_data(ctx, value)
        if data:
            return Member(data)
        raise fail("User", value)

    @property
    def tag(self) -> str:
        if self.discriminator:
            return f"{self.name}#{self.discriminator}"
        return self.name
    
    @property
    def display_name(self) -> str:
        return self.global_name or self.name

    async def create_dm(self) -> "DMChannel":
        from .channel import Channel
        
        data = await restapi.client.fetch_dm(str(self.id))
        return await Channel.from_dict(data)

    async def send(self, content:str, tts:bool = False):
        dm = await self.create_dm()
        return await dm.send(content, tts=tts)

    @property
    def channel(self) -> "_LazyDM":
        # Permite os dois usos: `await user.channel` e `await user.channel.send(...)`.
        return _LazyDM(self)
    
    def __str__(self) -> str:
        return self.display_name or self.global_name or self.name

    def __int__(self) -> int:
        return self.id.value

    def __repr__(self):
        return f"<User id={self.id.value} tag={self.tag} display_name={self.display_name}>"

class Member(User):
    def __init__(self, data:dict):
        user = data["user"]
        super().__init__(user)
        
        self.roles = data.get("roles", [])
        self.nick = data.get("nick")
        self.joined_at = data.get("joined_at")
        self.pending = data.get("pending", False)
        self.mute = data.get("mute", False)
        self.deaf = data.get("deaf", False)
        self.flags = data.get("flags", 0)

    @staticmethod
    async def convert(ctx, value:str) -> "Member":
        return Member(await find_member_data(ctx, value))

    @property
    def display_name(self):
        return self.nick

    def __str__(self) -> str:
        return self.display_name or self.nick or self.name or "None"

    def __int__(self) -> int:
        return self.id.value

    def __repr__(self):
        return f"<Member id={self.id.value} display_name={self.display_name} joined_at={self.joined_at}>"

class Author:
    def __new__(cls, data:dict):
        if "user" in data:
            return Member(data)
        return User(data)