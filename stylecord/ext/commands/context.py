from ...models.message import Message

class Context(Message):
    def __init__(self, data:dict | Message):
        if isinstance(data, Message):
            super().__init__(data.data, channel=data.channel, guild=data.guild)
        else:
            super().__init__(data)