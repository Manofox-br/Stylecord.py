from .._utils import restapi

from ..types.snowflake import Snowflake

from ..errors.errors import BadArgument
from ._utils.convert import find_channel_data

from .user import User

class Channel:
    def __init__(self, data:dict):
        id = data.get("id")
        self.id = Snowflake(id)
        guild_id = data.get("guild_id")
        self.guild_id = Snowflake(guild_id) if guild_id else None   # DMs não têm guild
        self.name = data.get("name")
        self.position = data.get("position", 0)
        self.parent_id = data.get("parent_id")
        self.raw_type = data.get("type")

    def __int__(self):
        return self.id.value

    def __str__(self):
        return self.name

    def __bool__(self):
        return self.id.value is not None
    
    def __repr__(self):
        return f"<Channel name={self.name!r} id={self.id.value} type={self.raw_type}>"

    @staticmethod
    async def from_dict(data:dict) -> "Channel":
        type = data.get("type", 0)

        match type:
            case 0:   # GuildText
                return TextChannel(data)
            
            case 1:   # DM
                return DMChannel(data)
            
            case 2:   # GuildVoice
                return VoiceChannel(data)
            
            case 3:   # GroupDM
                return GroupDMChannel(data)
            
            case 4:   # GuildCategory
                return CategoryChannel(data)
            
            case 5:   # GuildAnnouncement
                return AnnouncementChannel(data)
            
            case 10 | 11 | 12:  # Threads
                return ThreadChannel(data)
            
            case 13:  # StageVoice
                return StageChannel(data)
            
            case 14:  # Directory
                return DirectoryChannel(data)
            
            case 15:  # Forum
                return ForumChannel(data)
            
            case 16:  # Media
                return MediaChannel(data)
            
            case _:
                return Channel(data)

    @staticmethod
    async def convert(ctx, value:str) -> "Channel":
        data = await find_channel_data(ctx, value)
        return await Channel.from_dict(data) or Channel(data)

    async def send(self, content:str, tts:bool = False):
        from .message import Message
        msg = await restapi.client.send(
            str(self.id),
            content=content,
            tts=tts
        )
        
        return await Message.create(msg)

class TextChannel(Channel):
    def __init__(self, data:dict):
        super().__init__(data)
        self.last_message_id = data.get("last_message_id")
        self.flags = data.get("flags", 0)
        self.last_pin_timestamp = data.get("last_pin_timestamp")
        self.rate_limit_per_user = data.get("rate_limit_per_user", 0)
        self.topic = data.get("topic")
        self.permission_overwrites = data.get("permission_overwrites", [])
        self.nsfw = data.get("nsfw", False)

        self.type = TextChannel
    
    @staticmethod
    async def convert(ctx, value:str) -> "TextChannel":
        data = await find_channel_data(ctx, value, types=(0,))
        if data.get("type") != 0:
            raise BadArgument(f"'{value}' is not a text channel.")
        return TextChannel(data)

    def is_nsfw(self) -> bool:
        return self.nsfw

    def has_topic(self) -> bool:
        return self.topic is not None

class DMChannel(Channel):
    def __init__(self, data:dict):
        super().__init__(data)
        self.last_message_id = data.get("last_message_id")
        self.recipients = [User(r) for r in data.get("recipients", [])]
        self.flags = data.get("flags")

    #@classmethod
    #async def create(cls, data:dict):
    #    self = cls
    #    if data.recipients:
    #        self.recipients = [User(r) for r in data.get("recipients", [])]
    #
    #    return cls

    async def send(self, content:str, tts:bool = False):
        from .message import Message
        msg = await restapi.client.send(
            str(self.id),
            content=content,
            tts=tts
        )
        
        return await Message.create(msg)

# Tipos ainda sem recursos próprios: herdam tudo de Channel.
class GroupDMChannel(Channel): pass
class VoiceChannel(Channel): pass
class CategoryChannel(Channel): pass
class AnnouncementChannel(Channel): pass
class ThreadChannel(Channel): pass
class StageChannel(Channel): pass
class DirectoryChannel(Channel): pass
class ForumChannel(Channel): pass
class MediaChannel(Channel): pass
