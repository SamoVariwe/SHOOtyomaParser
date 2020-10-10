import requests
import aiohttp
from aiohttp import ClientSession
import asyncio
import json
import pickle
from datetime import datetime
import os
from bs4 import BeautifulSoup as bs
import time
from asyncio import Lock


batchSize=53
postURL='https://api.myshows.me/v2/rpc/'
baseShowUrl='https://myshows.me/view/'

# post Метод getIds не возвращает полный список всех id сериков, поэтому сначала получим список всех id и может сохраним его в файлик

#функции для получения id сериков
def GetShowsIdsAPI(SaveFileName)->list:
  pageSize=50 # кол-во сериков за заход
  page=-1
  showsIds=[]
  resultsQuantity=1
  getShowsData={
    "jsonrpc": "2.0",
    "method": "shows.Get",
    "params": {
      "search": {

      },
      "page": 0,
      "pageSize": pageSize
    },
    "id": 1
  }
  print(datetime.now())
  while resultsQuantity >0:
    if(page%50==0):
      print(page)
    page+=1
    getShowsData['params']['page']=page
    response = requests.post(postURL, json=getShowsData).json()
    resultsQuantity=len(response["result"])
    if resultsQuantity>0:
      resultList=response['result']
      for id in resultList:
        showsIds.append(id['id'])

  with open(SaveFileName,'wb') as file :
    pickle.dump(showsIds,file)
    print('IDs save in : '+SaveFileName+'\n')
    file.close()
  print(datetime.now())
  return showsIds

def GetShowIdsFromFile(PickleFileName)->list:
  try:
    with open(PickleFileName,'rb') as file:
      return pickle.load(file)
  except:
    print('No such file -> Getting ids from api')
    return GetShowsIdsAPI(PickleFileName)

def GetCursedIdsFromFile(cursedPath):
  with open(cursedPath,'r') as file:
    return  set(json.load(file))


#Ответ на шоу храни т id жанров, посему получим словарь id-жанр
def getGenres()->list:
  getGenresData = {
    "jsonrpc": "2.0",
    "method": "shows.Genres",
    "params": {},
    "id": 1
  }
  return requests.post(postURL,json=getGenresData).json()
lock=Lock()

#сохранение кортинки
def saveShowPh(phUrl,title):
  picName = title.replace(' ', '_').replace('*','_').replace(':','-').replace('/','-').replace('\t','').replace('\n','') + 'MAIN.jpg'
  image=requests.get(phUrl).content
  with open(os.getcwd() + '\\pics\\' + picName, 'wb') as saveFile:
    saveFile.write(image)
    saveFile.close()
  return picName

#получение кокнретных сериков по id


getByIdData={
  "jsonrpc": "2.0",
  "method": "shows.GetById",
  "params": {
    "showId": 0,
    "withEpisodes": True
  },
  "id": 1
}

getEpisodeByIdData={
  "jsonrpc": "2.0",
  "method": "shows.Episode",
  "params": {
    "id": 1
  },
  "id": 1
}



async def getEpisodeById(id: int,allEpisodes:list):
  global getEpisodeByIdData
  getEpisodeByIdData['params']['id'] = id
  session = ClientSession()
  async with session.post('https://api.myshows.me/v2/rpc/', json=getEpisodeByIdData) as resp:
    episode = await resp.json()
  await session.close()
  async with lock:
    allEpisodes.append(episode)


def getShow(id:int)->json:
  global getByIdData
  global getEpisodeByIdData
  showData={}
  getByIdData['params']['showId']=id
  result=requests.post(postURL,json=getByIdData).json()
  result=result['result']
  showData['ruTitle']=result['title']
  showData['enTitle']=result['titleOriginal']
  if showData['ruTitle']=="":
    showData['ruTitle']=showData['enTitle']
  showData['imdbRating']=result['imdbRating']
  showData['country'] = result['country']
  showData['startDate'] = result['started']
  showData['finishDate'] = result['ended']
  showData['releaseStatus'] = result['status']
  showData['description']=result['description']
  genresIds=result['genreIds']
  showGenres=[]
  for id in genresIds:
    for genre in genresIdToTitle['result']:
      if genre['id']==id:
        showGenres.append(genre['title'])
  showData['genres']=showGenres
  showData['totalDuration']=result['runtimeTotal']
  showData['episodeDuration']=result['runtime']
  picUrl=result['image']
  try:
    showData['picture']=saveShowPh(picUrl,showData['ruTitle'])
  except:
    showData['picture']='No Picture'
  try:
    showData['channel']=result['network']['title']
  except:
    showData['channel']='Нет информации о канале'
  episodesIds=[]
  for episodeId in result['episodes']:
    episodesIds.append(episodeId['id'])

  seasons=[]
  loop = asyncio.get_event_loop()
  tasks=[]
  allEpisodes = []

  batchNumber=int(len(episodesIds)/batchSize)
  for i in range(batchNumber+1):
    if i==batchNumber:
      try:
        for id in episodesIds[i * batchSize:]:
          task = asyncio.ensure_future(getEpisodeById(id, allEpisodes))
          tasks.append(task)
        loop.run_until_complete(asyncio.wait(tasks))
      except:
        pass
      tasks=[]
      time.sleep(0.5)
    else:
      for id in episodesIds[i*batchSize:(i+1)*batchSize]:
        task = asyncio.ensure_future(getEpisodeById(id, allEpisodes))
        tasks.append(task)
      loop.run_until_complete(asyncio.wait(tasks))
      tasks = []
      time.sleep(0.5)

  for seasonNumber in range(result['totalSeasons'],0,-1):
    season = {}
    season['episodes']=[]
    season['title']=showData['ruTitle']+': Сезон : '+str(seasonNumber)
    season['number']=seasonNumber
    isLastEpisode=True
    for episode in allEpisodes:
      if episode['result']['seasonNumber']<seasonNumber:
        break
      if episode['result']['seasonNumber']>seasonNumber:
        continue
      ourEpisode = {}
      anotherEpisode=episode['result']
      if isLastEpisode==True:
        try:
          season['finishDate']=anotherEpisode['airDate'][0:anotherEpisode['airDate'].find('T')]
        except:
          pass

        isLastEpisode=False

      ourEpisode['number']=anotherEpisode['shortName']
      ourEpisode['title']=anotherEpisode['title']
      try:
        ourEpisode['rating']=anotherEpisode['rating']['rating']
      except:
        pass
      try:
        ourEpisode['date']=anotherEpisode['airDate'][0:anotherEpisode['airDate'].find('T')]
      except:
        pass
      ourEpisode['imageURL']=anotherEpisode['image']
      a = anotherEpisode['episodeNumber']
      if anotherEpisode['episodeNumber'] <= 1:
        try:
          season['startDate'] = anotherEpisode['airDate'][0:anotherEpisode['airDate'].find('T')]
        except:
          pass

      if anotherEpisode['episodeNumber']==0:
        ourEpisode['isSpecial']=True
      else:
        ourEpisode['isSpecial']=False
      season['episodes'].append(ourEpisode)
    seasons.append(season)
  showData['seasons']=seasons
  return showData

mode=input('Проклятый режим? c / anyKey')



showsIds=[]#список id всех сериков
allShows=[]
if 'c' in mode:
  showsIds=GetCursedIdsFromFile('cursedIDS.json')
  print('Проклятых айдишек осталось: '+str(len(showsIds)))
  fileSubName='allCursedShows'
  lowId = int(input('нижняя граница среза: '))
  highId = int(input('верхняя граница среза (не включающая) : '))

else:
  showsIds=GetShowIdsFromFile('showsIds.data')
  lowId = int(input('нижняя граница среза: '))
  highId = int(input('верхняя граница среза (не включающая) : '))
  fileSubName='allShows'

genresIdToTitle=getGenres()

print(datetime.now())
serialN = -1

showsLeft=highId-lowId
cursedShowsIds=[]
normallyParsedCursedSHows=[]
try:
  with open(os.getcwd()+'\\jsons\\'+'cursedIDS.json','r') as cursedFile:
    cursedShowsIds=json.load(cursedFile)
except:
  print('проклятый Ясон пустой')
serialN = lowId-1
for i in showsIds[lowId:highId]:
  serialN+=1
  print('Осталось сериалов: '+str(showsLeft))

  try:
   data = getShow(i)
  except:
    print('Ошибочка случилась, id сохранен в файлик')

    try:
      with open(os.getcwd() + '\\jsons\\' + 'cursedIDS.json', 'r+') as cursedFile:
        cursedShowsIds = json.load(cursedFile)
        if i not in cursedShowsIds:
          cursedShowsIds.append(i)
        cursedFile.truncate(0)
        json.dump(cursedShowsIds,cursedFile)
    except:
      cursedShowsIds.append(i)
      with open(os.getcwd() + '\\jsons\\' + 'cursedIDS.json', 'w') as cursedFile:
        json.dump(cursedShowsIds,cursedFile)

    showsLeft -= 1
    continue

  allShows.append(data)
  if serialN%100==0:
    try:
      os.remove(jsonintermediateName)
    except:
      pass

    jsonintermediateName = os.getcwd() + '\\jsons\\' + fileSubName + str(lowId) + '_' + str(serialN) + '.json'
    jsonFile = open(jsonintermediateName, 'w')
    json.dump(allShows, jsonFile)
    jsonFile.close()
  showsLeft-=1
  normallyParsedCursedSHows.append(i)



print(datetime.now())
restShowsIds=[]
for id in showsIds:
  if id not in normallyParsedCursedSHows:
    restShowsIds.append(id)
with open('cursedIDS.json','w')as file:
  json.dump(restShowsIds,file)


try:
  os.remove(jsonintermediateName)
except:
  pass
jsonName=os.getcwd()+'\\jsons\\'+fileSubName+str(lowId)+'_'+str(highId)+'.json'
jsonFile=open(jsonName,'w')
json.dump(allShows,jsonFile)
with open(os.getcwd()+'\\jsons\\'+'cursedIDS.json','w') as cursedFile:
  json.dump(cursedShowsIds,cursedFile)

