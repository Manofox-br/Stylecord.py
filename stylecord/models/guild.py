from .._utils import restapi

from ..types.snowflake import Snowflake

from .emoji import Emoji
from .role import Role
from .sticker import Sticker
from .assets import Asset, GuildAssets
from .channel import Channel
from .user import User
from ._convert import find_guild_data

class Guild:
    def __init__(
        self,
        data:dict,
        afk_channel = None,
        system_channel = None,
        rules_channel = None,
        safety_alerts_channel = None,
        widget_channel = None,
        public_updates_channel = None,
        owner = None,
        members = None
    ):
        # === Identidade ===
        id = data.get("id")
        self.id = Snowflake(id)
        self.name = data.get("name")
        self.description = data.get("description")
        self.owner = owner
        self.region = data.get("region")
        self.widget_enabled = data.get("widget_enabled", False)
        self.mfa_level = data.get("mfa_level", 0)
        self.explicit_content_filter = data.get("explicit_content_filter", 0)
        self.default_message_notifications = data.get("default_message_notifications", 0)
        self.premium_subscription_count = data.get("premium_subscription_count", 0)
        self.nsfw_level = data.get("nsfw_level", 0)
        self.vanity_url_code = data.get("vanity_url_code")
        self.features = data.get("features", [])
        self.premium_tier = data.get("premium_tier", 0)
        self.members = {}
        
        # === Aparência ===
        icon_hash = data.get("icon")
        banner_hash = data.get("banner")
        splash_hash = data.get("splash")
        discovery_splash_hash = data.get("discovery_splash")
        home_banner_hash = data.get("home_banner")
        widget_image_hash = data.get("widget_image")
        application_command_badge_hash = data.get("application_command_badge")
        
        self.icon = Asset(f"icons/{id}/{icon_hash}.png") if icon_hash else Asset(None)
        self.banner = Asset(f"banners/{id}/{banner_hash}.png") if banner_hash else Asset(None)
        self.splash = Asset(f"splashes/{id}/{splash_hash}.png") if splash_hash else Asset(None)
        self.discovery_splash = Asset(f"discovery-splashes/{id}/{discovery_splash_hash}.png") if discovery_splash_hash else Asset(None)
        self.home_banner = Asset(f"home-banners/{id}/{home_banner_hash}.png") if home_banner_hash else Asset(None)
        self.widget_image = Asset(f"widget-images/{id}/{widget_image_hash}.png") if widget_image_hash else Asset(None)
        self.application_command_badge = Asset(f"application-command-badges/{id}/{application_command_badge_hash}.png") if application_command_badge_hash else Asset(None)
        self.guild_assets = guild_assets = GuildAssets(
            guild_id=self.id,
            icon_hash=icon_hash,
            banner_hash=banner_hash,
            splash_hash=splash_hash,
            discovery_splash_hash=discovery_splash_hash,
            home_banner_hash=home_banner_hash,
            widget_image_hash=widget_image_hash,
            application_command_badge_hash=application_command_badge_hash
        )
        
        # === Configuração de canais ===
        self.afk_channel = afk_channel
        self.afk_timeout = data.get("afk_timeout", 0)
        
        self.system_channel = system_channel
        self.system_channel_flags = data.get("system_channel_flags", 0)
        
        self.safety_alerts_channel = safety_alerts_channel
        self.rules_channel = rules_channel
        self.widget_channel = widget_channel
        self.public_updates_channel = public_updates_channel
        
        # === Segurança e verificação ===
        self.verification_level = data.get("verification_level", 0)
        self.max_members = data.get("max_members", 0)
        self.preferred_locale = data.get("preferred_locale", "en-US")

        # === Estruturas internas ===
        self.roles = [Role(r) for r in data.get("roles", [])]
        self.emojis = [Emoji(e) for e in data.get("emojis", [])]
        self.stickers = [Sticker(s) for s in data.get("stickers", [])]
        
    @classmethod
    async def create(cls, data:dict):
        self = cls(data)

        # AFK Channel
        afk_channel_id = data.get("afk_channel_id")
        if afk_channel_id:
            afk_channel_data = await restapi.client.fetch_channel(afk_channel_id)
            self.afk_channel = await Channel.from_dict(afk_channel_data)

        # System Channel
        system_channel_id = data.get("system_channel_id")
        if system_channel_id:
            system_channel_data = await restapi.client.fetch_channel(system_channel_id)
            self.system_channel = await Channel.from_dict(system_channel_data)

        # Rules Channel
        rules_channel_id = data.get("rules_channel_id")
        if rules_channel_id:
            rules_channel_data = await restapi.client.fetch_channel(rules_channel_id)
            self.rules_channel = await Channel.from_dict(rules_channel_data)

        # Safety Alerts Channel
        safety_alerts_channel_id = data.get("safety_alerts_channel_id")
        if safety_alerts_channel_id:
            safety_alerts_channel_data = await restapi.client.fetch_channel(safety_alerts_channel_id)
            self.safety_alerts_channel = await Channel.from_dict(safety_alerts_channel_data)

        # Public Updates Channel
        public_updates_channel_id = data.get("public_updates_channel_id")
        if public_updates_channel_id:
            public_updates_channel_data = await restapi.client.fetch_channel(public_updates_channel_id)
            self.public_updates_channel = await Channel.from_dict(public_updates_channel_data)

        # Owner
        owner_id = data.get("owner_id")
        if owner_id:
            owner_data = await restapi.client.fetch_user(owner_id)
            self.owner = User(owner_data)
        
        return self

    @staticmethod
    async def convert(ctx, value:str) -> "Guild":
        return await Guild.create(await find_guild_data(ctx, value))

    #===| FUNCTIONS |===#
    def get_member(self, member_id:Snowflake):
        if str(member_id) in self.members:
            return self.members[str(member_id)]
    
    def __int__(self):
        return self.id.value

    def __str__(self):
        return self.name

    def __bool__(self):
        return self.id.value is not None

    def __repr__(self):
        return f"<Guild name={self.name!r} id={self.id.value} owner={self.owner}>"
