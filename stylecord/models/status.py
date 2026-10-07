from enum import Enum

class StatusType(Enum):
    online = "online"
    idle = "idle"
    dnd = "dnd"
    invisible = "invisible"
    offline = "offline"

class Status:
    def __init__(self, afk:bool = False, status_type:StatusType = None):
        self._afk = afk
        self._type = status_type

    @property
    def value(self):
        return self._type.value if self._type else None

    @property
    def afk(self):
        return self._afk

    def __repr__(self):
        return f"<Status {self.value} afk={self.afk}>"

    online = None
    idle = None
    dnd = None
    invisible = None
    offline = None

    def __getattr__(self, name: str):
        if name in StatusType.__members__:
            return Status(self._afk, StatusType[name])
        raise AttributeError(f"No such status: {name}")

Status.online = Status(status_type=StatusType.online)
Status.idle = Status(status_type=StatusType.idle)
Status.dnd = Status(status_type=StatusType.dnd)
Status.invisible = Status(status_type=StatusType.invisible)
Status.offline = Status(status_type=StatusType.offline)