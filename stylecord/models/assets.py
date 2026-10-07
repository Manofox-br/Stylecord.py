from ..types.snowflake import Snowflake

class Asset:
    BASE_URL = "https://cdn.discordapp.com"

    def __init__(self, path:str):
        self._path = path

    @property
    def url(self) -> str | None:
        return f"{self.BASE_URL}/{self._path}" if self._path else None


class GuildAssets:
    def __init__(
        self,
        guild_id: Snowflake,
        icon_hash: str | None = None,
        splash_hash: str | None = None,
        discovery_splash_hash: str | None = None,
        banner_hash: str | None = None,
        home_banner_hash: str | None = None,
        widget_image_hash: str | None = None,
        application_command_badge_hash: str | None = None,
    ):
        self.guild_id = guild_id.value
        self.icon = Asset(f"icons/{guild_id}/{icon_hash}.png") if icon_hash else Asset(None)
        self.splash = Asset(f"splashes/{guild_id}/{splash_hash}.png") if splash_hash else Asset(None)
        self.discovery_splash = Asset(f"discovery-splashes/{guild_id}/{discovery_splash_hash}.png") if discovery_splash_hash else Asset(None)
        self.banner = Asset(f"banners/{guild_id}/{banner_hash}.png") if banner_hash else Asset(None)
        self.home_banner = Asset(f"home-banners/{guild_id}/{home_banner_hash}.png") if home_banner_hash else Asset(None)
        self.widget_image = Asset(f"widget-images/{guild_id}/{widget_image_hash}.png") if widget_image_hash else Asset(None)
        self.application_command_badge = Asset(f"application-command-badges/{guild_id}/{application_command_badge_hash}.png") if application_command_badge_hash else Asset(None)
        

class UserAssets:
    def __init__(
        self,
        user_id: Snowflake,
        avatar_hash: str | None = None,
        banner_hash: str | None = None,
        avatar_decoration_data: dict | None = None,
    ):
        self.user_id = user_id.value

        # Avatar (detecta animado)
        if avatar_hash:
            ext = "gif" if avatar_hash.startswith("a_") else "png"
            self.avatar = Asset(f"avatars/{user_id}/{avatar_hash}.{ext}")
        else:
            self.avatar = Asset(None)

        # Banner
        self.banner = Asset(f"banners/{user_id}/{banner_hash}.png") if banner_hash else Asset(None)

        # Avatar decoration  
        if avatar_decoration_data and avatar_decoration_data.get("asset"):
            self.avatar_decoration = Asset(
                f"avatar-decorations/{user_id}/{avatar_decoration_data['asset']}.png"
            )
        else:
            self.avatar_decoration = Asset(None)

class StickerAssets:
    def __init__(self, sticker_id, format_type):
        # format_type: 1 = PNG, 2 = APNG, 3 = Lottie
        if format_type == 1:
            self.asset = Asset(f"stickers/{sticker_id}.png")
        elif format_type == 2:
            self.asset = Asset(f"stickers/{sticker_id}.png")  # APNG
        elif format_type == 3:
            self.asset = Asset(f"stickers/{sticker_id}.json")
        else:
            self.asset = Asset(None)
