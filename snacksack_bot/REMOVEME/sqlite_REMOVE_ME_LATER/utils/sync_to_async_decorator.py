import asyncio


def make_async(func):
    async def wrapper(*args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    return wrapper
