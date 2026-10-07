from enum import IntEnum

class ActivityType(IntEnum):
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4

class Activity:
    def __init__(self, name: str, type: ActivityType = ActivityType.playing, url: str = None):
        self.name = name
        self.type = ActivityType(type)
        self.url = url

    def to_dict(self):
        if self.type == ActivityType.custom:
            return {
                "type": int(self.type),
                "name": "Custom Status",
                "state": self.name,
            }

        data = {"name": self.name, "type": int(self.type)}
        if self.url:
            data["url"] = self.url
        return data

    def __iter__(self):
        yield from self.to_dict().items()

    def __repr__(self):
        return f"<Activity type={self.type.name} name={self.name}>"