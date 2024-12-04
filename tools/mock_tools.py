import asyncio


async def mock_fetch_timeout(*args, **kwargs):
    raise asyncio.TimeoutError("Timeout error")