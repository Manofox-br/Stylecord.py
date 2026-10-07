from .exceptions import StylecordWarnings

class NotInstaledWarning(StylecordWarnings):
    def __init__(self, lib:str):
        # f"Optional library not installed. ({lib})"
        pass