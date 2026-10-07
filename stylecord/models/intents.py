FLAGS = {
    "guilds":               1 << 0,
    "members":              1 << 1,
    "bans":                 1 << 2,
    "emojis":               1 << 3,
    "integrations":         1 << 4,
    "webhooks":             1 << 5,
    "invites":              1 << 6,
    "voice_states":         1 << 7,
    "presences":            1 << 8,
    "messages":             1 << 9,
    "message_reactions":    1 << 10,
    "message_typing":       1 << 11,
    "direct_messages":      1 << 12,
    "dm_reactions":         1 << 13,
    "dm_typing":            1 << 14,
    "message_content":      1 << 15,
}

class Intents:
    GROUPS = {
        "guild": ["guilds", "members", "bans", "emojis", "integrations", "webhooks", "invites", "voice_states", "presences"],
        "messages": ["messages", "message_reactions", "message_typing", "message_content"],
        "direct": ["direct_messages", "dm_reactions", "dm_typing"],
    }

    def __init__(self, **kwargs):
        self._value = 0
        for key, val in kwargs.items():
            if key not in FLAGS:
                raise ValueError(f"The intent '{key}' does not exist.")
            if not isinstance(val, bool):
                raise TypeError(f"The value of '{key}' must be bool, not {type(val).__name__}.")
            if val:
                self._value |= FLAGS[key]

    @classmethod
    def all(cls):
        obj = cls()
        obj._value = sum(FLAGS.values())
        return obj

    @classmethod
    def default(cls):
        return cls()

    def __int__(self):
        return self._value

    def __repr__(self):
        ativos = [k for k, v in FLAGS.items() if self._value & v]
        return f"Intents(ativos={ativos}, valor={self._value})"

    def _get_flag(self, name):
        return bool(self._value & FLAGS[name])

    def _set_flag(self, name, value):
        if not isinstance(value, bool):
            raise TypeError(f"Valor de '{name}' deve ser bool, não {type(value).__name__}.")
        if value:
            self._value |= FLAGS[name]
        else:
            self._value &= ~FLAGS[name]

for flag in FLAGS:
    setattr(Intents, flag,
            property(lambda self, f=flag: self._get_flag(f),
                     lambda self, val, f=flag: self._set_flag(f, val)))