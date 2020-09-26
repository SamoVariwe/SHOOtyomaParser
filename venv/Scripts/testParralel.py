import aiohttp
import asyncio
from datetime import datetime
import time


async def get(url):
    print("Getting :"+url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print("Ready :" + url)
            return response

print(datetime.now().second)
loop = asyncio.get_event_loop()

coroutines = [get("https://myshows.me/view/7718/") for _ in range(20)]

results = loop.run_until_complete(asyncio.gather(*coroutines))
print(datetime.now())
print("Results: %s" % results)