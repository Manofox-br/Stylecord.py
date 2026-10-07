from .exceptions import StylecordException
from .._utils import tools

colors = tools.Colors

class InvalidTokenError(StylecordException):
    def __init__(self, reason:str = None):
        #super().__init__(f"{colors.blue}Discord{colors.reset} Token is not {colors.red}invalid{colors.reset} or has {colors.yellow}expired{colors.reset}.", reason=reason, code=401)
        super().__init__(f"Discord Token is not invalid or has expired.", reason=reason, code=401)

class MissingIntent(StylecordException):
    def __init__(self, intent_name:str, reason:str = None):
        #super().__init__(f"The intent {colors.cyan}'{intent_name}'{colors.reset} is required, but not enabled.", reason=reason, code=403)
        super().__init__(f"The intent {colors.cyan}'{intent_name}'{colors.reset} is required, but not enabled.", reason=reason, code=403)

class NotInstaledError(StylecordException):
    def __init__(self, lib:str):
        super().__init__(f"Optional library '{lib}' not installed.", code=404)

class BadArgument(StylecordException):
    def __init__(self, msg:str, reason:str = None):
        super().__init__(msg, reason=reason, code=400)
        self.message = msg 