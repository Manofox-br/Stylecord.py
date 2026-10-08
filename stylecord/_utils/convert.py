import re

from .._utils import restapi

from ..errors.discord_errors import NotFound
from ..errors.errors import BadArgument

RAW_ID = re.compile(r"^\d{15,22}$")
CHANNEL_MENTION = re.compile(r"^<#(\d+)>$")
USER_MENTION = re.compile(r"^<@!?(\d+)>$")
ROLE_MENTION = re.compile(r"^<@&(\d+)>$")
EMOJI_MENTION = re.compile(r"^<(a?):(\w{2,32}):(\d+)>$")

def match_id(value:str, mention:re.Pattern) -> str | None:
    value = value.strip()
    m = mention.match(value)
    if m:
        return m.group(1)
    if RAW_ID.match(value):
        return value
    return None

def fail(kind:str, value:str, reason:str = None) -> BadArgument:
    return BadArgument(f"{kind} '{value}' not found.", reason=reason)

def require_guild(ctx, kind:str):
    guild = getattr(ctx, "guild", None)
    if not guild:
        raise BadArgument(f"{kind} conversion only works inside a server.")
    return guild

async def _get_json(path:str, **params):
    rc = restapi.client
    r = await rc.httpx_client.get(f"{rc._rest_api}{path}", headers=rc.headers, params=params or None)
    return r.json()

#===| CHANNELS |===#
async def find_channel_data(ctx, value:str, types:tuple | None = None) -> dict:
    cid = match_id(value, CHANNEL_MENTION)
    if cid:
        try:
            data = await restapi.client.fetch_channel(cid)
        except NotFound:
            raise fail("Channel", value)

        if not isinstance(data, dict) or "id" not in data:
            raise fail("Channel", value)
        return data

    guild = require_guild(ctx, "Channel")
    name = value.strip().lstrip("#").replace(" ", "-").lower()
    rc = restapi.client

    # 1) cache
    if rc._cache_channels is not None:
        for data, _ in list(rc._cache_channels.values()):
            if str(data.get("guild_id")) == str(guild.id) and (data.get("name") or "").lower() == name:
                if types is None or data.get("type") in types:
                    return data

    # 2) REST
    try:
        channels = await _get_json(f"/guilds/{guild.id}/channels")
    except NotFound:
        raise fail("Channel", value)

    if isinstance(channels, list):
        for data in channels:
            data.setdefault("guild_id", str(guild.id))
            if (data.get("name") or "").lower() == name and (types is None or data.get("type") in types):
                return data

    raise fail("Channel", value)

#===| USERS / MEMBERS |===#
async def find_user_data(ctx, value:str) -> dict:
    uid = match_id(value, USER_MENTION)
    if not uid:
        raise fail("User", value)

    try:
        data = await restapi.client.fetch_user(uid)
    except NotFound:
        raise fail("User", value)

    if not isinstance(data, dict) or "id" not in data:
        raise fail("User", value)
    return data

async def search_member_data(ctx, value:str) -> dict | None:
    guild = getattr(ctx, "guild", None)
    query = value.strip().lstrip("@")
    if not guild or not query:
        return None

    try:
        found = await _get_json(f"/guilds/{guild.id}/members/search", query=query, limit=10)
    except NotFound:
        return None

    if not isinstance(found, list):
        return None

    q = query.lower()
    for m in found:
        user = m.get("user") or {}
        names = {(m.get("nick") or "").lower(), (user.get("username") or "").lower(), (user.get("global_name") or "").lower()}
        if q in names:
            return m
    return None

async def find_member_data(ctx, value:str) -> dict:
    guild = require_guild(ctx, "Member")
    uid = match_id(value, USER_MENTION)

    if uid:
        try:
            data = await restapi.client.fetch_member(str(guild.id), uid)
        except NotFound:
            raise fail("Member", value)

        if not isinstance(data, dict) or "user" not in data:
            raise fail("Member", value)
        return data

    data = await search_member_data(ctx, value)
    if not data:
        raise fail("Member", value)
    return data

#===| GUILDS |===#
async def find_guild_data(ctx, value:str) -> dict:
    gid = match_id(value, re.compile(r"^(\d+)$"))
    if gid:
        try:
            data = await restapi.client.fetch_guild(gid)
        except NotFound:
            raise fail("Server", value)

        if not isinstance(data, dict) or "id" not in data:
            raise fail("Server", value)
        return data

    rc = restapi.client
    name = value.strip().lower()
    if rc._cache_guilds is not None and name:
        for data, _ in list(rc._cache_guilds.values()):
            if (data.get("name") or "").lower() == name:
                return data

    raise fail("Server", value)
