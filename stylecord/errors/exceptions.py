from .._utils import tools

colors = tools.Colors

class DiscordException(Exception):
    def __init__(self, msg:str = None, reason:str = None, code:int = None):
        base_msg = f"{colors.bold}{colors.cyan}Discord Exception{colors.reset}"

        if msg:
            base_msg += f" ─ {colors.red}{msg}{colors.reset}"

        if reason:
            base_msg += f" {colors.bold}{colors.red}({reason}){colors.reset}"

        super().__init__(base_msg)
        self.code = code

    def __str__(self):
        if self.code is not None:
            return f"{colors.bold}{colors.yellow}[Error {self.code}]{colors.reset} {self.args[0]}"
        return self.args[0]

class StylecordException(Exception):
    def __init__(self, msg:str = None, reason:str = None, code:int = None):
        base_msg = f"{colors.bold}{colors.blue}Stylecord Exception{colors.reset}"

        if msg:
            base_msg += f" ─ {colors.red}{msg}{colors.reset}"

        if reason:
            base_msg += f" {colors.bold}{colors.red}({reason}){colors.reset}"

        super().__init__(base_msg)
        self.code = code

    def __str__(self):
        if self.code is not None:
            return f"{colors.bold}{colors.yellow}[Error {self.code}]{colors.reset} {self.args[0]}"
        return self.args[0]

class StylecordWarnings:
    pass