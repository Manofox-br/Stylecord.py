import inspect, importlib

def command(name=None, aliases=None, prefixes=None):
    def decorator(func):
        func.__stylecord_command__ = {
            "name": name or func.__name__,
            "aliases": aliases or [],
            "prefixes": prefixes or [],
        }
        return func
    return decorator

def listener(event_name=None):
    def decorator(func):
        func.__stylecord_listener__ = event_name or func.__name__
        return func
    return decorator

class Cog:
    command = staticmethod(command)
    listener = staticmethod(listener)

    def __init__(self, bot=None):
        self.bot = bot

    def _collect(self):
        commands, listeners = {}, {}

        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            cmd = getattr(method, "__stylecord_command__", None)
            if cmd:
                commands[cmd["name"]] = {
                    "func": method,
                    "aliases": list(cmd["aliases"]),
                    "prefixes": list(cmd["prefixes"]),
                }

            event = getattr(method, "__stylecord_listener__", None)
            if event:
                listeners.setdefault(event, []).append(method)

        return commands, listeners

    @classmethod
    async def load(cls, bot):
        self = cls(bot)
        cog_name = cls.__name__

        self.commands, self.listeners = self._collect()
        bot.cogs[cog_name] = self

        for cmd_name, cmd_data in self.commands.items():
            cmd_data["prefixes"] = cmd_data["prefixes"] or [bot.prefix]
            bot.commands[cmd_name] = cmd_data

        for event_name, func in self.listeners.items():
            bot.events.setdefault(event_name, []).extend(func)
        
        return self

    async def unload(self):
        cog_name = self.__class__.__name__
        
        cog = self.bot.cogs.pop(cog_name)
        if cog:
            for cmd_name in self.commands:
                self.bot.commands.pop(cmd_name, None)

            for event_name, funcs in self.listeners:
                if event_name in self.bot.events:
                    for func in funcs:
                        if func in self.bot.events[event_name]:
                            self.bot.events[event_name].remove(func)

    async def reload(self):
        bot = self.bot

        await self.unload()
        await self.__class__.load(bot)