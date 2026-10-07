from ..types.snowflake import Snowflake

from .assets import StickerAssets, Asset

class Sticker:
    def __init__(self, data:dict):
        id = data.get("id")
        self.id = Snowflake(id)
        self.name = data.get("name")
        self.tags = data.get("tags")
        self.type = data.get("type")
        self.format_type = data.get("format_type")
        self.description = data.get("description")
        asset = data.get("asset")

        if self.format_type == 1:
            self.asset = Asset(f"stickers/{id}.png")
        elif self.format_type == 2:
            self.asset = Asset(f"stickers/{id}.png")  # APNG
        elif self.format_type == 3:
            self.asset = Asset(f"stickers/{id}.json")
        else:
            self.asset = Asset(None)
        
        self.sticker_asset = StickerAssets(self.id.value, self.format_type)
        self.available = data.get("available", False)
