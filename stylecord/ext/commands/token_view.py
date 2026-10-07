class TokenView:
    def __init__(self, content: str):
        self.content = content
        self.index = 0

    def skip_whitespace(self):
        while self.index < len(self.content) and self.content[self.index].isspace():
            self.index += 1

    def next_token(self):
        self.skip_whitespace()
        if self.index >= len(self.content):
            return None

        start = self.index
        while self.index < len(self.content) and not self.content[self.index].isspace():
            self.index += 1
        return self.content[start:self.index]

    def read_rest(self):
        self.skip_whitespace()
        rest = self.content[self.index:]
        self.index = len(self.content)
        return rest