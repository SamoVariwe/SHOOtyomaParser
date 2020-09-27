from bs4 import BeautifulSoup as bs
import requests
import json
import os
from datetime import datetime
import asyncio
import aiohttp
import async_timeout


proxys=['79.143.30.163:8080','46.151.108.6:41171','49.51.52.170:8888','119.2.41.81:8080',
        '96.114.249.38:3128','190.214.27.46:8080','181.6.225.130:1080','175.6.149.195:1080','81.88.220.110:3128',
        '62.171.177.113:8888','49.87.18.84:38801','117.68.195.33:1080','91.211.107.204:41258','35.169.156.54:3128',
        '193.41.88.58:53281','103.233.158.34:8888','36.91.58.109:8080','47.112.230.91:1080','202.162.197.110:8888',
        '92.46.63.232:3128','77.104.250.189:43394','180.109.124.30:4216','219.140.119.201:1080','8.129.219.138:1080',
        '64.120.89.48:1080','188.166.248.24:1080','147.78.160.2:8080','177.192.162.80:3128']

ProxyNumber=-1

class classClearHTML():#название обусловлено структурой сайта
    pass

async def AllShowsParse(shows,lock):
    ret=await asyncio.gather(*[ShowParse(show,lock) for show in shows])


async def ShowParse(show,lock:asyncio.Lock):
    showA = show.find('a')
    ref = showA.get('href')
    global ProxyNumber
    ProxyNumber+=1
#    with session.get(ref) as response:
    async with aiohttp.ClientSession() as session:
        async with session.get(url=ref) as response:
            showPage=await response.text()


    showSoup = bs(showPage, features='html.parser')
    description = showSoup.find('div', {'class': 'col5'}).find('p').text
    ruTitle = showSoup.find('h1', attrs={'itemprop': 'name'}).text  # русское название
    status = showSoup.find('h1', attrs={'itemprop': 'name'}).find('sup').get('title')  # статус сериалла
    enTitle = showSoup.find('p', attrs={'class': 'subHeader'}).text  # нерусское название
    print('Сейчас парсится сериалл: ' + enTitle + '\n')


    classClearhtml = showSoup.find('div', {'class': 'clear'})  # такое очевидное название в честь вот этого самого

    clearClassObject = await classClearhtmlParser(
        classClearhtml)  # получение обьекта класса, способного вытянуть нужную информацю
    # с этого обьекта
    # save main photo
    if len(enTitle) != 0:

        picName = enTitle.replace(' ', '_').replace('*', 'U') + '_MAIN.jpg'

    else:
        picName = ruTitle.replace(' ', '_') + '_MAIN.jpg'
    with open(os.getcwd() + '\\pics\\' + picName, 'wb') as saveFile:
        saveFile.write(clearClassObject.image)
        saveFile.close()
    # Season rows
    seasonRows = showSoup.find_all('div', attrs={'itemprop': 'season'})
    seasonsObjects = []

    for season in seasonRows[::-1]:
        seasonObject = {}
        episodesObjects = []
        titleNumObject = season.find('h2', attrs={'itemprop': 'name', 'class': 'flat'})
        seasonObject['number'] = titleNumObject.text  # номер сезона
        async with aiohttp.ClientSession() as session:
            async with session.get('https://myshows.me' + titleNumObject.find('a').get('href')) as response:
                seasonPageText = await response.text()



        seasonPageSoup = bs(seasonPageText,
                            features="html.parser")  # страница сезона
        tempText = seasonPageSoup.find('h1').text  # название сезона
        seasonObject['title'] = tempText[:len(tempText) - 4]  # название сезона - 4 символа года выпуска
        # ща дата пойдет
        episodeDates = season.find_all('span', attrs={'class': '_date', 'itemprop': 'datePublished'})
        seasonObject['startDate'] = episodeDates[-1].get('content')
        seasonObject['finishDate'] = episodeDates[0].get('content')
        # начинаем хрюкаться с эпизодами
        episodesRows = season.find_all('li', attrs={'itemprop': 'episode'})
        for episodeRow in episodesRows[::-1]:
            try:
                episodeRef = episodeRow.find_all('a')[1].get('href')
            except IndexError:
                episodeRef = episodeRow.find_all('a')[0].get('href')
            async with aiohttp.ClientSession() as episodeSession:
                async with episodeSession.get(episodeRef) as response:
                    episodeText = await response.text()
            #episodeText=requests.get(episodeRef).text
            episodeSoup = bs(episodeText, features='html.parser')
            episode = {}
            mainSoup = episodeSoup.find('main', {'role': 'main'})
            numberPlusTitle = mainSoup.find('h1').text
            episode['number'] = numberPlusTitle[0:numberPlusTitle.find('—')]
            episode['title'] = numberPlusTitle[numberPlusTitle.find('—') + 1:]
            clearEpisodeSoup = mainSoup.find('div', {'class': 'clear'})
            psEpisodeSoup = clearEpisodeSoup.find_all('p')
            for pEpisodeSoup in psEpisodeSoup[1:]:
                if str(pEpisodeSoup).find('Рейтинг') or str(pEpisodeSoup).find('Rating'):
                    try:
                        episode['rating'] = pEpisodeSoup.text
                    except IndexError:
                        episode['rating'] = 'Нет рейтинга'

            try:
                episode['startEpisode'] = psEpisodeSoup[0].find('sup').text.split(' ')[0]
            except:
                episode['startEpisode'] = 'Не указано'

            episodeImageUrl = getImageUrl(clearEpisodeSoup)
            # episode['image'] = requests.get(episodeImageUrl).content
            episode['imageUrl'] = episodeImageUrl
            if len(enTitle) != 0:
                episodePicName = enTitle.replace(' ', '_').replace('*', 'U') + episode['number'].replace(' ',
                                                                                                         '_') + '.jpg'
            else:
                episodePicName = ruTitle.replace(' ', '_') + episode['number'].replace(' ', '_') + '.jpg'
            # with open(os.getcwd() + '\\episodes\\' + episodePicName, 'wb') as saveFile:
            #     saveFile.write(episode['image'])
            #     saveFile.close()
            episode['picture'] = episodePicName
            # del episode['image']
            episodesObjects.append(episode)
            seasonObject['episodes'] = episodesObjects
        seasonsObjects.append(seasonObject)

    data = {"ruTitle": ruTitle,
            "enTitle": enTitle,
            "description": description,
            "country": clearClassObject.country,
            "startDate": clearClassObject.startDate,
            "finishDate": clearClassObject.finishDate,
            "releaseStatus": status,
            "genres": clearClassObject.genres,
            "totalDuration": clearClassObject.totalDuration,
            "episodeDuration": clearClassObject.episodeDuration,
            "picture": picName,
            "channel": clearClassObject.channel,
            "seasons": seasonsObjects

            }
    print('Отпарсился : '+enTitle+'\n')
    async with lock:
        showsJson.append(data)

def dateParsesr(date:str):
    date=date[date.find(':')+1:]
    startDate=date[0:date.find('–')]
    finishDate = date[date.find('–')+1:]
    return startDate,finishDate

def getImageUrl(clearClassObject:bs)->str:
    imageUrl = clearClassObject.find('div', attrs={'class': 'presentBlockImg'}).get('style')
    if imageUrl==None:
        return 'http://mol27.ru/wp-content/uploads/2017/01/velichayshaya_oshibka.jpg'
    imageUrl = imageUrl[imageUrl.find('(') + 1:len(imageUrl) - 1]
    return imageUrl


async def  classClearhtmlParser(htmlClassClear:bs)->classClearHTML:
    clearObject=classClearHTML()
    imageUrl=getImageUrl(htmlClassClear)

    async with aiohttp.ClientSession() as session:
        async with session.get(imageUrl) as response:
            a= await response.read()
            clearObject.image=a
    ps=htmlClassClear.find_all('p')
    clearObject.startDate,clearObject.finishDate=dateParsesr(ps[0].text)#в 0 хранится дата
    clearObject.country=ps[1].text[ps[1].text.find(':')+1:]#страна
    genresRaw=ps[2].text.replace(' ','')[ps[2].text.find(':')+2:]
    clearObject.genres=genresRaw.split(',')
    clearObject.channel = ps[3].text[ps[3].text.find(':') + 1:]  # страна
    clearObject.totalDuration=ps[5].text[ps[5].text.find(':') + 1:]
    clearObject.episodeDuration = ps[6].text[ps[6].text.find(':') + 1:]
    return clearObject


#Тут почали
startPageNumber=int(input('укажите первую страницу парсинга: \n'))
finishPageNumber=int(input('укажите последнюю страницу парсинга: \n'))
print(datetime.now())

basePageUrl='https://en.myshows.me/search/all/?category=show&page='
clearJson=open('test.json','w')
clearJson.close()

showsJson=[]
for pageNumber in range(startPageNumber,finishPageNumber+1):
    print('Сейчас парсится страница: '+str(pageNumber)+'\n')
    mainPageUrl=basePageUrl+str(pageNumber-1)
    mainPageHTML=requests.get(mainPageUrl).text
    soupPage=bs(mainPageHTML,features="html.parser")



    #get shows list on a page
    table=soupPage.findChildren(name='table',attrs={'class': 'catalogTable'})
    table=table[1]#без понятия, почему так, хотя нет, знаю, но что делать не знаю
    shows=(table.findChildren(name='tr'))

    # showRefs=[]
    #
    # for show in shows[1:]:
    #     showA=show.find('a')
    #     showRefs.append(showA.get('href'))


    lock=asyncio.Lock()

    asyncio.get_event_loop().run_until_complete(AllShowsParse(shows[1:3],lock))


with open('test.json',"a",encoding='utf_8') as jsonFile:
    json.dump(showsJson,jsonFile,ensure_ascii=False)
print('всё')
print(datetime.now())


