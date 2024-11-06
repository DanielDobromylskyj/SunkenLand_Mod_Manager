import time
from functools import wraps


def cache_with_timeout(timeout):
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = (args, frozenset(kwargs.items()))
            current_time = time.time()

            # Check if it's in our cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]

                # Check if timeout has expired
                if current_time - timestamp < timeout:
                    return result

            # Call the function and store the result with the current timestamp
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            return result

        return wrapper
    return decorator
