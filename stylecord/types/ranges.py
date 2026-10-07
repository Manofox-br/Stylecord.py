class TupleRange(tuple):
    def __new__(cls, start:int, maximum:int = None):
        if isinstance(start, tuple) and maximum is None:
            start, maximum = start

        if not isinstance(start, int) or not isinstance(maximum, int):
            raise TypeError("TupleRange only accepts integers.")
        if start < 0 or maximum < start:
            raise ValueError("Invalid tuple range: start >= 0 and maximum >= start")

        obj = super().__new__(cls, (start, maximum))
        obj.start = start
        obj.maximum = maximum
        return obj

    def next_delay(self, attempt:int, max_attempts:int) -> int:
        if attempt <= 1:
            return self.start
        
        ratio = min(attempt / max_attempts, 1.0)
        return int(self.start + (self.maximum - self.start) * ratio)

    def __iter__(self):
        return iter((self.start, self.maximum))

    def __repr__(self):
        return f"TupleRange(start={self.start}, maximum={self.maximum})"