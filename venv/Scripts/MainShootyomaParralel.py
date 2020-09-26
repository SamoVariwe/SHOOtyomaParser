from bs4 import BeautifulSoup as bs
import requests
import json
import os
import aiohttp
import asyncio
from datetime import datetime


class classClearHTML():#название обусловлено структурой сайта
    pass

class Seasons():
    pass

class Episode():
    pass

async def getShowResponse(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response

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


def classClearhtmlParser(htmlClassClear:bs)->classClearHTML:
    clearObject=classClearHTML()
    imageUrl=getImageUrl(htmlClassClear)
    clearObject.image=requests.get(imageUrl).content
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
if startPageNumber==finishPageNumber:
    finishPageNumber+=1
basePageUrl='https://en.myshows.me/search/all/?category=show&page='
clearJson=open('test.json','w')
clearJson.close()
timeDot=datetime.now()
showsJson=[]
for pageNumber in range(startPageNumber,finishPageNumber):
    print('Сейчас парсится страница: '+str(pageNumber)+'\n')
    timeDot=datetime.now()-timeDot
    print(timeDot)
    mainPageUrl=basePageUrl+str(pageNumber-1)
    mainPageHTML=requests.get(mainPageUrl).text
    soupPage=bs(mainPageHTML,features="html.parser")


    #вот тут бы насрать переключением страниц

    #get shows list on a page
    table=soupPage.findChildren(name='table',attrs={'class': 'catalogTable'})
    table=table[1]#без понятия, почему так, хотя нет, знаю, но что делать не знаю
    shows=(table.findChildren(name='tr'))

    showRefs=[]

    for show in shows[1:]:
        showA=show.find('a')
        showRefs.append(showA.get('href'))


    for show in shows[1:]:

        showPage = requests.get(ref).text
        showSoup=bs(showPage,features='html.parser')
        description=showSoup.find('div',{'class':'col5'}).find('p').text
        ruTitle=showSoup.find('h1',attrs={'itemprop':'name'}).text#русское название
        status=showSoup.find('h1',attrs={'itemprop':'name'}).find('sup').get('title')#статус сериалла
        enTitle=showSoup.find('p',attrs={'class':'subHeader'}).text#нерусское название
        print('Сейчас парсится сериалл: '+enTitle+'\n')
        timeDot = datetime.now() - timeDot
        print(timeDot)
        classClearhtml=showSoup.find('div',{'class':'clear'})#такое очевидное название в честь вот этого самого

        clearClassObject=classClearhtmlParser(classClearhtml)#получение обьекта класса, способного вытянуть нужную информацю
        #с этого обьекта
        #save main photo
        if len(enTitle)!=0:

            picName = enTitle.replace(' ', '_').replace('*','U') + '_MAIN.jpg'

        else:
            picName = ruTitle.replace(' ', '_') + '_MAIN.jpg'
        with open(os.getcwd()+'\\pics\\'+picName,'wb') as saveFile:
            saveFile.write(clearClassObject.image)
            saveFile.close()
        #Season rows
        seasonRows=showSoup.find_all('div',attrs={'itemprop':'season'})
        seasonsObjects=[]

        for season in seasonRows[::-1]:
            seasonObject={}
            episodesObjects=[]
            titleNumObject=season.find('h2',attrs={'itemprop':'name','class':'flat'})
            seasonObject['number']= titleNumObject.text#номер сезона
            seasonPageSoup=bs(requests.get('https://myshows.me'+titleNumObject.find('a').get('href')).text,features="html.parser")#страница сезона
            tempText=seasonPageSoup.find('h1').text#название сезона
            seasonObject['title']=tempText[:len(tempText)-4]#название сезона - 4 символа года выпуска
            #ща дата пойдет
            episodeDates=season.find_all('span',attrs={'class':'_date','itemprop':'datePublished'})
            seasonObject['startDate']=episodeDates[-1].get('content')
            seasonObject['finishDate'] = episodeDates[0].get('content')
            #начинаем хрюкаться с эпизодами
            episodesRows=season.find_all('li',attrs={'itemprop':'episode'})
            for episodeRow in episodesRows[::-1]:
                try:
                    episodeRef=episodeRow.find_all('a')[1].get('href')
                except IndexError:
                    episodeRef = episodeRow.find_all('a')[0].get('href')
                episodeSoup=bs(requests.get(episodeRef).text,features='html.parser')
                episode={}
                mainSoup=episodeSoup.find('main',{'role':'main'})
                numberPlusTitle=mainSoup.find('h1').text
                episode['number']=numberPlusTitle[0:numberPlusTitle.find('—')]
                episode['title']=numberPlusTitle[numberPlusTitle.find('—')+1:]
                clearEpisodeSoup=mainSoup.find('div',{'class':'clear'})
                psEpisodeSoup=clearEpisodeSoup.find_all('p')
                for pEpisodeSoup in psEpisodeSoup[1:]:
                    if str(pEpisodeSoup).find('Рейтинг') or str(pEpisodeSoup).find('Rating'):
                        try:
                            episode['rating'] = pEpisodeSoup.text
                        except IndexError:
                            episode['rating'] = 'Нет рейтинга'

                try:
                    episode['startEpisode']=psEpisodeSoup[0].find('sup').text.split(' ')[0]
                except:
                    episode['startEpisode']='Не указано'

                episodeImageUrl=getImageUrl(clearEpisodeSoup)
                episode['image'] = requests.get(episodeImageUrl).content
                if len(enTitle)!=0:
                    episodePicName = enTitle.replace(' ', '_').replace('*','U') + episode['number'].replace(' ','_')+'.jpg'
                else:
                    episodePicName = ruTitle.replace(' ', '_') + episode['number'].replace(' ', '_') + '.jpg'
                with open(os.getcwd() + '\\episodes\\' + episodePicName, 'wb') as saveFile:
                    saveFile.write(episode['image'])
                    saveFile.close()
                episode['picture']=episodePicName
                del episode['image']
                episodesObjects.append(episode)
                seasonObject['episodes']=episodesObjects
            seasonsObjects.append(seasonObject)


        data={ "ruTitle": ruTitle,
        "enTitle": enTitle,
         "description":description,
         "country": clearClassObject.country,
         "startDate": clearClassObject.startDate,
         "finishDate": clearClassObject.finishDate,
         "releaseStatus":status,
         "genres":clearClassObject.genres,
         "totalDuration":clearClassObject.totalDuration,
         "episodeDuration":clearClassObject.episodeDuration,
         "picture":picName,
         "channel":clearClassObject.channel,
         "seasons":seasonsObjects


        }
        showsJson.append(data)


with open('test.json',"w",encoding='utf_8') as jsonFile:
    json.dump(showsJson,jsonFile,ensure_ascii=False)
print('всё')

