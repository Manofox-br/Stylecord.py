import asyncio, logging, inspect
from pydantic import validate_call
from typing import List

from ._utils import checkers, core, restapi
from .errors import errors

from .types.snowflake import Snowflake
from .types.token import Token

from .models.channel import Channel
from .models.client_user import ClientUser
from .models.intents import Intents
from .models.message import Message
from .models.guild import Guild
from .models.user import Member
from .models.status import Status
from .models.activity import Activity

from .ext.decorators.retry import async_retry

class Client:
    def __init__(self, intents:"Intents" | None = None):
        # Basic information
        self.user = None
        self.id = None
        self.username = None
        self.discriminator = None
        self.avatar = None
        self.global_name = None

        # Session
        self._session_id = None
        self.session_type = None
        self.resume_gateway_url = None

        # Guilds and channels
        self.guilds = []
        self.private_channels = []
        self.relationships = []
        self.presences = []

        # Additional settings
        self.latency = None
        self.user_settings = {}
        self.application = None
        self.geo_ordered_rtc_regions = []
        self.game_relationships = []
        self.auth = {}

        # Internal control
        if isinstance(intents, Intents): self.intents = intents
        else: raise TypeError(f"{intents} is not valid.")
        self.events = {}
        self.trace = []

    def event(self, name=None):
        if callable(name):                      # @bot.event
            self.events[name.__name__] = name
            return name
    
        def decorator(func):                    # @bot.event("on_ready") / @bot.event()
            self.events[name or func.__name__] = func
            return func
        return decorator
    
    async def dispatch(self, event_name, *args, **kwargs):
        def _log_task_error(task:asyncio.Task):
            try:
                exc = task.exception()
            except asyncio.CancelledError:
                logging.debug(f"Task '{event_name}' canceled.")
                return
            
            if exc is None:
                return
            elif isinstance(exc, asyncio.CancelledError):
                logging.debug(f"Task {event_name} canceled.")
            else:
                logging.exception(f"Error in '{event_name}':\n{exc}")
        
        handler = self.events.get(event_name)
        if handler:
            task = asyncio.create_task(handler(*args, **kwargs))
            task.add_done_callback(_log_task_error)
                
    def __repr__(self):
        return (
            f"<Client "
            f"username={self.username or 'None'}#{self.discriminator or 'None'} "
            f"id={self.id or 'None'} "
            f"guilds={len(self.guilds) if self.guilds else 0} "
            f"session_id={self._session_id or 'None'} "
            f"seq={self.s or 'None'}>"
        )
        
    #===| HANDLES |===#
    async def handle_connect(self):
        await self.dispatch("on_connect")
    
    async def handle_ready(self, data:dict):
        async def _load_guilds(guild_dicts):
            #fetch_guilds_dicts = [await restapi.client.fetch_guild(g["id"]) for g in guild_dicts]
            #self.guilds = [await Guild.create(fg) for fg in fetch_guilds_dicts]
            tasks = [restapi.client.fetch_guild(g["id"]) for g in guild_dicts]
            fetch_guilds_dicts = await asyncio.gather(*tasks, return_exceptions=True)

            for fg in fetch_guilds_dicts:
                guild = await Guild.create(fg)
                self.guilds.append(guild)
                        
        self.t = data.get("t")
        self.s = data.get("s")
        self.op = data.get("op")
        d = data.get("d", {})

        # Version
        self.v = d.get("v") if d else None

        # User
        user = d.get("user", {})
        self.user = ClientUser(user)
        
        # Session
        self._session_id = d.get("session_id")
        self.session_type = d.get("session_type")
        self.resume_gateway_url = d.get("resume_gateway_url")

        # Structures
        self.user_settings = d.get("user_settings", {})
        self.relationships = d.get("relationships", [])
        self.private_channels = d.get("private_channels", [])
        self.presences = d.get("presences", [])
        guild_dicts = d.get("guilds", [])
        self.guilds = []
        self.guild_join_requests = d.get("guild_join_requests", [])
        self.geo_ordered_rtc_regions = d.get("geo_ordered_rtc_regions", [])
        self.game_relationships = d.get("game_relationships", [])
        self.auth = d.get("auth", {})
        self.application = d.get("application", {})
        self.trace = d.get("_trace", [])

        asyncio.create_task(_load_guilds(guild_dicts))
        asyncio.create_task(restapi.client._load_cache(d))
        await self.dispatch("on_ready")

    async def handle_pong(self, ping=None):
        self.latency = ping
        await self.dispatch("on_pong", ping)

    async def handle_message(self, data):
        message = await Message.create(data)
        await self.dispatch("on_message", message)
    
    #===| FUNCTIONS |===#
    # • fetchs • #
    async def fetch_channel(self, channel_id:Snowflake, force:bool = False) -> "Channel":
        if not self.intents._get_flag("guilds"):
            raise errors.MissingIntents("guilds")
        
        data = await restapi.client.fetch_channel(str(channel_id), force)
        channel = await Channel.from_dict(data)

        return channel

    async def fetch_guild(self, guild_id:Snowflake, force:bool = False) -> "Guild":
        if not self.intents._get_flag("guilds"):
            raise errors.MissingIntents("guilds")
        
        data = await restapi.client.fetch_guild(str(guild_id), force)
        guild = Guild.create(data)

        return guild

    async def fetch_members(self, guild_id:Snowflake, force:bool = False):
        if not self.intents._get_flag("members"):
            raise errors.MissingIntents("members")

        data = await restapi.client.fetch_members(str(guild_id), force)
        members = [Member(m) for m in data]

        return members

    async def fetch_member(self, guild_id:Snowflake, user_id:Snowflake, force:bool = False):
        if not self.intents._get_flag("members"):
            raise errors.MissingIntents("members")

        data = await restapi.client.fetch_member(str(guild_id), str(user_id), force)
        member = Member(data)

        return member

    # • status • #
    async def set_status(self, activity:Activity, status:Status = Status.online):
        await self._conn.set_status([activity], status)

    @async_retry(max_attempts=3, delay=(1, 30))
    async def cycle_status(self, activities:List[Activity], next_status:int | float = 12, status:Status = Status.online):
        while True:
            for activity in activities:
                prioritized = self.prioritize_activity(activities, activity)
                await self._conn.set_status(prioritized, status)
                await asyncio.sleep(next_status)
    
    def prioritize_activity(self, activities:List[Activity], first:Activity) -> list[Activity]:
        activities = [a for a in activities if a.name != first.name]
        return [first] + activities

    # • outhers • #
    async def ping(self, timeout:int = 60):
        latency = await self._conn.send_ping(timeout)
        return latency
    
    # • run • #
    @validate_call
    async def start(self, token:Token):
        if hasattr(self, "setup_hook"):
            func = getattr(self, "setup_hook")
            if callable(func) and inspect.iscoroutinefunction(func):
                await func()
        
        self._conn = core.Connection(self)
        await self._conn.login(token, self.intents)
        
    def run(self, token):
        try: asyncio.run(self.start(token))
        except KeyboardInterrupt: pass
        