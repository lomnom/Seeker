"""
Shared log function.

Set DO_LOG to False to silence logging.
"""
import time

red = "\033[31m"
green = "\033[32m"
no_color = "\033[0m" 
START = time.perf_counter()

DO_LOG = True
def log(*args, **kwargs):
    """Logs messages with a timestamp since startup. Same syntax as print."""
    timestamp = time.perf_counter() - START
    timestamp = round(timestamp, 2)
    timestamp = str(timestamp).ljust(8, " ") + "s"
    timestamp = f"[{timestamp}]" 
    timestamp = "\033[2m" + timestamp + "\033[22m" # make dim.

    print(timestamp, *args, **kwargs)