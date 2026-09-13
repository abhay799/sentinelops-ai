import asyncio
import selectors
import sys


def sentinelops_loop_factory() -> asyncio.AbstractEventLoop:
    """
    Create an event loop compatible with SentinelOps dependencies.

    Psycopg async requires SelectorEventLoop on Windows.
    Other operating systems use their normal asyncio loop.
    """
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())

    return asyncio.new_event_loop()