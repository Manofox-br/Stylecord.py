from .user import User

class ClientUser(User):
    def __init__(self, data: dict):
        super().__init__(data)

        self.bot = data.get("bot", False)
        self.verified = data.get("verified", False)
        self.email = data.get("email")
        self.mfa_enabled = data.get("mfa_enabled", False)
        self.flags = data.get("flags", 0)
        self.application = data.get("application", {})
        self.primary_guild = data.get("primary_guild")
        self.session_id = data.get("session_id")

    def __repr__(self):
        return (
            f"<ClientUser id={self.id.value} tag={self.tag} "
            f"display_name={self.display_name} bot={self.bot}>"
        )
