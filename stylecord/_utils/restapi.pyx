import httpx, time, logging
from collections import OrderedDict, deque

from ..errors import discord_errors
from ..errors.exceptions import DiscordException

async def log_request(request):
    return

async def log_response(response):
    match response.status_code:
        case 404:
            raise discord_errors.NotFound("Not found.")

        case 403:
            raise discord_errors.Forbiden("Unknown or without permission.")

        case 429:
            raise discord_errors.TooManyRequests("Timeout reached, too many requests.")

async def log_error(exc):
    if isinstance(exc, httpx.ReadError):
        return

    else:
        logging.error(exc)

httpx_hook = {
    "request": [log_request],
    "response": [log_response],
    "error": [log_error]
}

class DiscordRESTClient:
    def __init__(
        self, 
        token, 
        intents, 
        max_channels = None, 
        max_guilds = None,
        max_members = None,
        max_users = None,
        max_dm = None,
        max_messages = 1000
    ):
        
        self.headers = {"Authorization": f"Bot {token}"}
        self._rest_api = "https://discord.com/api/v10"
        self.httpx_client = httpx.AsyncClient(event_hooks=httpx_hook)
        self.intents = intents

        self.max_channels = max_channels
        self.max_guilds = max_guilds
        self.max_messages = max_messages
        self.max_members = max_members
        self.max_users = max_users
        self.max_dm = max_dm
        
        #===| CACHES |===#
        self._cache_channels: OrderedDict[str, tuple[dict, float]] = OrderedDict() if intents._get_flag("guilds") else None
        self._cache_guilds: OrderedDict[str, tuple[dict, float]] = OrderedDict() if intents._get_flag("guilds") else None
        self._cache_members: OrderedDict[str, tuple[dict, float]] = OrderedDict() if intents._get_flag("members") else None
        self._cache_messages: dict[str, deque[tuple[dict, float]]] = {} if intents._get_flag("messages") else None
        self._cache_users: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._cache_dm: OrderedDict[str, tuple[dict, float]] = OrderedDict() if intents._get_flag("direct_messages") else None
        
    async def _load_cache(self, data:dict):
        if not self.intents._get_flag("guilds"):
            return

        now = time.time()
        for guild_data in data.get("guilds", []):
            guild_id = guild_data["id"]
            self._cache_guilds[guild_id] = (guild_data, now)

            for channel_data in guild_data.get("channels", []):
                channel_id = channel_data["id"]
                self._cache_channels[channel_id] = (channel_data, now)

    async def close(self):
        global client
        await self.httpx_client.aclose()
        client = None
                
    #===| FETCHS |===#
    async def fetch_channel(self, channel_id:str, force:bool = False):
        now = time.time()
        use_cache = force or self.intents._get_flag("guilds")
        
        if not use_cache and channel_id in self._cache_channels:
            data, ts = self._cache_channels[channel_id]
            ttl = 3600 * 6 if data.get("last_message_id") else 900
            if now - ts < ttl:
                return data
        
        r = await self.httpx_client.get(
            f"{self._rest_api}/channels/{channel_id}",
            headers=self.headers
        )
        data = r.json()

        if self._cache_channels is not None:
            self._cache_channels[channel_id] = (data, now)
            self._cache_channels.move_to_end(channel_id)
            if self.max_channels and len(self._cache_channels) > self.max_channels:
                self._cache_channels.popitem(last=False)
        
        return data

    async def fetch_guild(self, guild_id:str, force:bool = False):
        now = time.time()
        use_cache = force or self.intents._get_flag("guilds")

        if not use_cache and guild_id in self._cache_guilds:
            data, ts = self._cache_guilds[guild_id]
            ttl = 3600 * 6 if data.get("channels") else 900
            if now - ts < ttl:
                return data

        r = await self.httpx_client.get(
            f"{self._rest_api}/guilds/{guild_id}",
            headers=self.headers
        )
        data = r.json()

        if self._cache_guilds is not None:
            self._cache_guilds[guild_id] = (data, now)
            self._cache_guilds.move_to_end(guild_id)
            if self.max_guilds and len(self._cache_guilds) > self.max_guilds:
                self._cache_guilds.popitem(last=False)

        return data

    async def fetch_member(self, guild_id:str, user_id:str = None, force:bool = False):
        now = time.time()
        use_cache = force or self.intents._get_flag("members")

        key = (guild_id, user_id)
        if not use_cache and key in self._cache_members:
            data, ts = self._cache_members[key]
            ttl = 3600 * 6 if data.get("roles") or data.get("joined_at") else 900
            if now - ts < ttl:
                return data

        r = await self.httpx_client.get(
            f"{self._rest_api}/guilds/{guild_id}/members/{user_id}",
            headers=self.headers
        )
        data = r.json()

        if self._cache_members is not None:
            self._cache_members[key] = (data, now)
            self._cache_members.move_to_end(key)
            if self.max_members and len(self._cache_members) > self.max_members:
                self._cache_members.popitem(last=False)

        return data

    async def fetch_members(self, guild_id:str, force:bool = False):
        now = time.time()
        use_cache = force or self.intents._get_flag("members")

        key = (guild_id, None)
        if not use_cache and key in self._cache_members:
            data, ts = self._cache_members[key]
            ttl = 3600 * 6 if any(m.get("roles") or m.get("joined_at") for m in data) else 900
            if now - ts < ttl:
                return data

        members = []
        after = None

        while True:
            params = {"limit": 1000}
            if after:
                params["after"] = after

            r = await self.httpx_client.get(
                f"{self._rest_api}/guilds/{guild_id}/members",
                headers=self.headers,
                params=params
            )
            chunk = r.json()

            if not chunk:
                break

            members.extend(chunk)

            if len(chunk) < 1000:
                break

            after = chunk[-1]["user"]["id"]

        self._cache_members[key] = (members, now)
        self._cache_members.move_to_end(key)
        if self.max_members and len(self._cache_members) > self.max_members:
            self._cache_members.popitem(last=False)

        return members

    async def fetch_user(self, user_id: str, force: bool = False):
        now = time.time()
        use_cache = force
        
        if not use_cache and user_id in self._cache_users:
            data, ts = self._cache_users[user_id]
            ttl = 3600 * 6 if data.get("global_name") or data.get("avatar") else 900
            if now - ts < ttl:
                return data

        r = await self.httpx_client.get(
            f"{self._rest_api}/users/{user_id}",
            headers=self.headers
        )
        data = r.json()

        self._cache_users[user_id] = (data, now)
        self._cache_users.move_to_end(user_id)
        if self.max_users and len(self._cache_users) > self.max_users:
            self._cache_users.popitem(last=False)

        return data

    async def fetch_dm(self, user_id:str, force:bool = False):
        now = time.time()
        use_cache = force or self.intents._get_flag("direct_messages")

        if use_cache and user_id in self._cache_dm:
            data, ts = self._cache_dm[user_id]
            ttl = 3600 * 6 if data.get("last_message_id") else 900
            if now - ts < ttl:
                return data

        payload = {"recipient_id": user_id}

        r = await self.httpx_client.post(
            f"{self._rest_api}/users/@me/channels",
            headers=self.headers,
            json=payload
        )
        data = r.json()
        
        self._cache_dm[user_id] = (data, now)
        self._cache_dm.move_to_end(user_id)
        if self.max_dm and len(self._cache_dm) > self.max_dm:
            self._cache_dm.popitem(last=False)

        return data

    #===| SENDS |===#
    async def send(
        self, 
        channel_id:str, 
        message_reference:str = None,
        embeds = None,
        components = None,
        attachments = None,
        parse = None,
        replied:bool = False,
        content:str = None,
        tts:bool = False
    ):
        payload = {"tts": tts}
        if content:
            payload["content"] = content
        if message_reference:
            payload["message_reference"] = {"message_id": message_reference}
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components
        if parse:
            payload.setdefault("allow_mentions", {})["parse"] = parse
        if replied:
            payload.setdefault("allow_mentions", {})["replied_user"] = replied
        if attachments:
            payload["attachments"] = attachments
        
        r = await self.httpx_client.post(
            f"{self._rest_api}/channels/{channel_id}/messages",
            headers=self.headers,
            json=payload
        )
        data = r.json()

        if r.status_code >= 400:
            raise DiscordException(data.get("message"), code=data.get("code") or r.status_code)

        return data

    #===| MESSAGES |===#
    def add_message_to_cache(self, channel_id:str, message_data:dict):
        if self._cache_messages is None:
            return

        now = time.time()
        if channel_id not in self._cache_messages:
            self._cache_messages[channel_id] = deque(maxlen=self.max_messages)
        
        self._cache_messages[channel_id].append((message_data, now))

    #===| GETS |===#
    def get_messages(self, channel_id:str, ttl:int | None = None):
        if self._cache_messages is None:
            return []

        msgs = self._cache_messages.get(channel_id, [])
        if ttl:
            now = time.time()
            return [msg for msg, ts in msgs if now - ts < ttl]
        
        return [msg for msg, _ in msgs]

client: DiscordRESTClient | None = None

def init_client(token, intents):
    global client
    client = DiscordRESTClient(token, intents)