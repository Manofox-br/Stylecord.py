import asyncio, functools, random, logging

from ...types.ranges import TupleRange

def async_retry(max_attempts:int = 3, delay:TupleRange | tuple = TupleRange(1, 10)):
    if isinstance(delay, tuple):
        delay = TupleRange(*delay)
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay.start
            
            for attempt in range(max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    current_delay = delay.next_delay(attempt, max_attempts)
                    await asyncio.sleep(current_delay + random.uniform(0, 0.9))
                    logging.warning(f"Attempt failed: {e}, retry in {current_delay}s...")

            raise RuntimeError(f"Too many attempts during retry.")
        return wrapper
    return decorator