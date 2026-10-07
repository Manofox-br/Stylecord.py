import asyncio
#from datetime import datetime 

from .._utils import restapi
from ..types.snowflake import Snowflake

from .channel import Channel
from .guild import Guild
from .user import Member, User, Author

class Message:
    def __init__(self, data:dict, channel=None, guild=None, member=None):
        # Identificação básica
        id = data.get("id")
        self.id = Snowflake(id)
        self.data = data
        self.content = data.get("content")
        self.timestamp = data.get("timestamp")
        self.edited_timestamp = data.get("edited_timestamp")
        self.tts = data.get("tts", False)
        self.pinned = data.get("pinned", False)
        self.nonce = data.get("nonce")
        self.type = data.get("type", 0)
        self.flags = data.get("flags", 0)

        # Objetos relacionados
        self.member = member
        self.channel = channel
        self.guild = guild
        self.author = Author(data.get("author", {}))
        self.user = User(data.get("author", {}))
        if guild and not self.member:
            member_data = dict(data.get("member") or {})
            member_data["user"] = data.get("author", {})
            self.member = Member(member_data)
            
        # Listas
        self.mentions = data.get("mentions", [0])
        self.mention_roles = data.get("mention_roles", [])
        self.mention_everyone = data.get("mention_everyone", False)
        self.embeds = data.get("embeds", [])

    @classmethod
    async def create(cls, data:dict):
        d = data.get("d") or data
        self = cls(d)

        channel_id = d.get("channel_id")
        if channel_id:
            channel_data = await restapi.client.fetch_channel(channel_id)
            self.channel = await Channel.from_dict(channel_data)

        guild_id = d.get("guild_id")
        if guild_id:
            guild_data = await restapi.client.fetch_guild(guild_id)
            self.guild = await Guild.create(guild_data)
        
        return self

    async def send(self, content:str, tts:bool = False):
        msg = await restapi.client.send(
            str(self.channel.id),
            content=content,
            tts=tts
        )

        return await Message.create(msg)

    async def reply(self, content:str, tts:bool = False):
        msg = await restapi.client.send(
            str(self.channel.id),
            message_reference=str(self.id),
            content=content,
            tts=tts
        )
        
        return await Message.create(msg)

    def __int__(self):
        return self.id.value
        
    def __str__(self):
        return self.content

    def __bool__(self):
        return self.id.value is not None
    
    def __repr__(self):
        return f"<Message id={self.id.value} author={self.author.name} content={self.content!r}>"
