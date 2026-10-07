import re
from datetime import datetime

DISCORD_EPOCH = 1420070400000 # 2015-01-01T00:00:00Z

class Snowflake(int):
    def __new__(cls, value:int | str):
        return super().__new__(cls, int(value))

    @staticmethod
    async def convert(ctx, value) -> Snowflake:
        match = re.search(r"\d{17,19}", str(value))
        if not match:
            raise ValueError(f"The argument '{argument}' is not a valid Snowflake.")
        return Snowflake(int(match.group(0)))
    
    @property
    def timestamp(self) -> float:
        return ((int(self) >> 22) + DISCORD_EPOCH) / 1000

    @property
    def datetime(self):
        return datetime.utcfromtimestamp(self.timestamp)

    @property
    def worker_id(self) -> int:
        return (int(self) >> 17) & 0x1F

    @property
    def process_id(self) -> int:
        return (int(self) >> 12) & 0x1F

    @property
    def increment(self) -> int:
        return int(self) & 0xFFF

    @property
    def value(self) -> int:
        return int(self)

    def __int__(self):
        return super().__int__()

    def __str__(self):
        return str(int(self))