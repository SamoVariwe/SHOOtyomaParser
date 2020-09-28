import aiohttp
from aiohttp import ClientSession
import asyncio
import json
import pickle

showsIds=[]
file=open('showsIds.data','rb')
showsIds=pickle.load(file)

shows=[]

tasks=[]

getByIdData={
  "jsonrpc": "2.0",
  "method": "shows.GetById",
  "params": {
    "showId": 0,
    "withEpisodes": True
  },
  "id": 1
}

async def getShow(id:int):
    print(id)
    global getByIdData
    getByIdData['params']['showId']=id
    session=ClientSession()
    async with session.post('https://api.myshows.me/v2/rpc/',json=getByIdData) as resp:
        show=await resp.json()
    await session.close()


    shows.append(show)
loop=asyncio.get_event_loop()

for id in showsIds[0:50]:
    task=asyncio.ensure_future(getShow(id))
    tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))

print('aue')



