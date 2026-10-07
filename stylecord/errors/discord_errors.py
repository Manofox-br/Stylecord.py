from .exceptions import DiscordException

class NotFound(DiscordException):
    def __init__(self, msg=None):
        super().__init__(msg, code=404)

class Forbiden(DiscordException):
    def __init__(self, msg=None):
        super().__init__(msg, code=403)

class TooManyRequests(DiscordException):
    def __init__(self, msg=None):
        super().__init__(msg, code=429)