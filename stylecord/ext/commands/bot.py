import inspect, importlib

from ...client import Client

from ...models.message import Message

from .context import Context
from .token_view import TokenView
from .cogs import Cog

class Bot(Client):
    def __init__(self, prefix:str = None, intents:"Intents" | None = None):
        super().__init__(intents)
        self.prefix = prefix
        self.commands = {}
        self.cogs = {}

    def command(self, name=None, aliases=None, prefixes=None):
        def decorator(func):
            cmd_name = name or func.__name__
            cmd_aliases = aliases or []
            cmd_prefixes = prefixes or [self.prefix]

            self.commands[cmd_name] = {
                "func": func,
                "aliases": cmd_aliases,
                "prefixes": cmd_prefixes,
            }

            return func
        return decorator

    async def handle_message(self, data:dict):
        message = await Message.create(data)
        if "on_message" in self.events:
            await self.dispatch("on_message", message)
        else:
            await self.process_commands(message)

    async def process_commands(self, message:Message):
        content = message.content
        tv = TokenView(content)
        first = tv.next_token()
        if not first:
            return
    
        for cmd_name, cmd_data in self.commands.items():
            for prefix in cmd_data["prefixes"]:
                if not first.startswith(prefix):
                    continue
    
                name = first[len(prefix):]
                if name == cmd_name or name in cmd_data["aliases"]:
                    ctx = Context(message)
                    func = cmd_data["func"]
                    return await self.invoke(ctx, func, tv)

    async def run_converters(self, ctx, ann, raw):
        if ann is inspect._empty:
            return raw
    
        if ann in (int, float, str):
            try:
                return ann(raw)
            except Exception:
                return raw
    
        if hasattr(ann, "convert"):
            return await ann.convert(ctx, raw)
    
        if callable(ann):
            if inspect.iscoroutinefunction(ann):
                return await ann(ctx, raw)
            else:
                return ann(raw)
    
        return raw
    
    async def invoke(self, ctx:Context, func, tv:TokenView):
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        converters = {
            int: int,
            float: float,
            str: str,
        }
    
        args = []
        kwargs = {}
    
        for i, param in enumerate(params):
            ann = param.annotation
            kind = param.kind
    
            if i == 0:
                args.append(ctx)
                continue
    
            if kind == inspect.Parameter.VAR_POSITIONAL:  # *args
                collected = []
                while True:
                    raw = tv.next_token()
                    if raw is None:
                        break
                    collected.append(raw)
                args.extend(collected)
                continue
    
            if kind == inspect.Parameter.VAR_KEYWORD:  # **kwargs
                while True:
                    raw = tv.next_token()
                    if raw is None:
                        break
                    if "=" in raw:
                        k, v = raw.split("=", 1)
                        kwargs[k] = v
                continue
    
            if kind == inspect.Parameter.KEYWORD_ONLY:
                kwargs[param.name] = tv.read_rest()
                continue
    
            raw = tv.next_token()
            if raw is None:
                args.append(param.default if param.default is not inspect._empty else None)
                continue
    
            val = await self.run_converters(ctx, ann, raw)
            args.append(val)
    
        return await func(*args, **kwargs)

    def add_converter(type_, func):
        converters[type_] = func

    #===| COGS |===#
    async def add_cog(self, module_name:str):
        mod = importlib.import_module(module_name)

        if hasattr(mod, "setup"):
            setup_func = mod.setup
            if inspect.iscoroutinefunction(setup_func):
                await setup_func(self)
            else:
                setup_func(self)
        else:
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if (
                    isinstance(obj, type) and
                    issubclass(obj, Cog) and
                    obj is not Cog
                ):
                    await obj.load(self)
    
    def __repr__(self):
        return (
            f"<Bot "
            f"username={self.username or 'None'}#{self.discriminator or 'None'} "
            f"id={self.id or 'None'} "
            f"prefix={self.prefix or 'None'} "
            f"guilds={len(self.guilds) if self.guilds else 0} "
            f"session_id={self._session_id or 'None'} "
            f"seq={self.s or 'None'}>"
        )
