import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
import urllib
import numpy as np
import json

def clean_up_string(string):

    string = string.replace('\xa0', ' ')
    string = string.strip()

    for char in [':', ';', '!', '?', '«', '»']:
        string = re.sub(r'\s\{}'.format(char), '&nbsp;{}'.format(char), string)
    for char in ['«']:
        string = re.sub(r'\{}\s'.format(char), '{}&nbsp;'.format(char), string)

    return string.strip()

def clean_up_review(elem):

    string = str(elem)
    string = re.sub('</(span|div|font)>', '', string)
    string = string.replace('<div style="text-align: justify;">', '')
    string = string.replace('<div style="text-align: left;">', '')
    string = string.replace('<span style="font-size:16px">', '')
    string = string.replace('<span style="color:#808080">', '')
    string = string.replace('<span style="color:#444444">', '')
    string = string.replace('<span style="font-family:trebuchet ms,lucida grande,lucida sans unicode,lucida sans,tahoma,sans-serif">', '')
    string = string.replace('<span style="font-family:lora,georgia,times new roman,serif">', '')
    string = string.replace('<font color="#444444" face="lora, georgia, times new roman, serif">', '')
    string = string.replace('<span style="color: #444444;font-family: lora,georgia,times new roman,serif;text-align: justify;">', '')
    string = string.replace('mso-line-height-rule: exactly;-ms-text-size-adjust: 100%;-webkit-text-size-adjust: 100%;', '')
    string = string.replace('text-size-adjust: 100%;', '')
    string = string.replace(' style=""', '')
    string = string.replace(' style="color: #007C89;font-weight: normal;text-decoration: underline;" ', '')

    string = clean_up_string(string)

    return string

def clean_up_week(week):
    week = re.sub("</span>", "", week)
    week = re.sub("</div>", "", week)
    week = re.sub('"font-size:16px"', "", week)
    week = re.sub('"color:#444444"', "", week)
    week = re.sub('"font-family:lora,georgia,times new roman,serif"', "", week)
    week = re.sub('"text-align: left;"', "", week)
    week = re.sub('<span style=>', '', week)
    week = re.sub('<div style=>', '', week)
    return week

base_url = 'https://us6.campaign-archive.com/home/?u=00a9245e71d3375ef4542a588&id=3270cdb251'

html = requests.get(base_url)
print(html.status_code)
soup = BeautifulSoup(html.content, 'html.parser')

links = {}
for elem in soup.find_all(class_ = 'campaign'):
    links[elem.text[6:10]+"-"+elem.text[3:5]+"-"+elem.text[:2]] = elem.find('a').get('href')

links['2021-08-18'] = links['2021-08-19']
del links['2021-08-19']

#links['2021-08-11'] = links['2021-08-12']
#del links['2021-08-12']

for elem in links.keys():
    if datetime.strptime(elem, "%Y-%m-%d").date().weekday() != 2:
        print("clean up {} (must be a Wednesday)".format(elem))


print("\nCOLLECTING REVIEWS:")
date_list, image_list, category_list, movie_list, review_list, showtime_list, id_list = [], [], [], [], [], [], []
for date, link in links.items():

    try:
        html = requests.get(link)
        soup = BeautifulSoup(html.content, 'html.parser')

        date_l, image_l, category_l, movie_l, review_l, showtime_l, id_l = [], [], [], [], [], [], []

        i=1
        texts = soup.findAll(class_ = 'mcnImageCardBlock')
        for text in texts:
            date_l.append(date)

            cat_movie = text.find('h3').text

            if len(cat_movie.split('\n'))>1:
                category_l.append(cat_movie.split('\n')[0].strip())
                movie_l.append(cat_movie.split('\n')[1].strip())
            else:
                category_l.append(cat_movie.split(':')[0].strip())
                movie_l.append(cat_movie.split(':')[1].strip())
            review_l.append(clean_up_review(text.find(class_ = 'mcnTextContent').findAll('div')[0]))
            showtime_l.append(clean_up_string(text.find(class_ = 'mcnTextContent').findAll('div')[-1].text.strip()))

            current_id = "id_" + str(date).replace('-', '') + "_" + str(i)
            image_url = text.find(class_ = 'mcnImage').get('src')
            id_l.append(current_id)
            image_l.append(image_url)
            urllib.request.urlretrieve(image_url, "../website_cine/img/reviews/" + current_id + ".png")

            i += 1

        date_list += date_l
        image_list += image_l
        category_list += category_l
        movie_list += movie_l
        review_list += review_l
        showtime_list += showtime_l
        id_list += id_l

    except:
        print('{} Failed'.format(date))

reviews = pd.DataFrame({
    'id': id_list,
    'date': date_list,
    'category': category_list,
    'movie': movie_list,
    'review': review_list,
    'showtime': showtime_list,
    'image': image_list,
})
reviews = reviews.sort_values(['date', 'id'], ascending=[False, True]).reset_index(drop=True)

reviews.loc[
    reviews['movie']=='"Bonnie and Clyde", par Arthur Penn\xa0(1967)', 'movie'
] = "Bonnie and Clyde, Arthur Penn (1967)"
reviews.loc[
    reviews['movie']=='"La Rue de la honte", par Kenji Mizoguchi (1956)', 'movie'
] = "La Rue de la honte, Kenji Mizoguchi (1956)"

reviews.loc[
    (reviews['movie']=="Bonnie and Clyde, Arthur Penn (1967)")&(reviews['date']=="2021-07-28"), 'review'
] = "Le film qui a chamboul\u00e9 la critique am\u00e9ricaine et lanc\u00e9 le Nouvel Hollywood est toujours aussi percutant aujourd'hui.<blockquote>\u00ab&nbsp;Audiences [...] are not given a simple, secure basis for identification; they are made to feel but are not told how to feel. \u201cBonnie and Clyde\u201d is not a serious melodrama involving us in the plight of the innocent but a movie that assumes [...] that we don\u2019t need to pretend we\u2019re interested only in the falsely accused, as if real criminals had no connection with us.&nbsp;\u00bb</blockquote><blockquote style=\"text-align: right;\">- <a href=\"https://www.newyorker.com/magazine/1967/10/21/bonnie-and-clyde\"target=\"_blank\">Pauline Kael, The New Yorker, 1967</a></blockquote>"
reviews.loc[
    (reviews['movie']=="L'enfance nue,\u00a0Maurice Pialat (1969)")&(reviews['date']=="2021-08-04"), 'review'
] = "Le premier film de Maurice Pialat, ressorti dans le cadre d'une retrospective en cours, est une p\u00e9pite. En choisissant principalement des acteurs non-professionnels, Pialat emploie un style quasi-documentaire pour dresser un portrait doux-amer de l'enfance sous la R\u00e9publique fran\u00e7aise des ann\u00e9es 60.<blockquote>\u00ab&nbsp;J'\u00e9tais inconscient. Tout \u00e9tait r\u00e9uni pour que ca ne marche pas. Moi, en tant que spectateur, je n'y serais pas all\u00e9&nbsp;!&nbsp;\u00bb</blockquote><blockquote style=\"text-align: right;\">- Maurice Pialat</blockquote>"
reviews.loc[
    (reviews['movie']=="Mother,\u00a0Bong Joon Ho\u00a0(2009)")&(reviews['date']=="2021-08-18"), 'review'
] = "<blockquote>\u00ab&nbsp;Malgr\u00e9 ces ruptures de tons et de genres, malgr\u00e9 ses constantes surprises psychologiques et sc\u00e9naristiques, <em>Mother</em> garde le cap tendu de son suspense polaro-filial et maintient une tenue formelle impeccable&nbsp;: beaut\u00e9 des plans, virtuosit\u00e9 du montage, des changements d\u2019intensit\u00e9, des glissements entre burlesque et tragique.&nbsp;\u00bb</blockquote><blockquote style=\"text-align: right;\">- <a href=\"https://www.lesinrocks.com/cinema/mother-25894-22-01-2010/\"target=\"_blank\">Serge Kaganski, Les Inrockuptibles, 2010</a></blockquote>"

reviews['movie_name'] = reviews['movie'].apply(lambda x: ','.join(x.split(',')[:-1]))
reviews['movie_directors'] = reviews['movie'].apply(lambda x: re.sub('\(.+\)', '', x.split(',')[-1]).strip())
reviews['movie_year'] = reviews['movie'].apply(lambda x: x.split(',')[-1][-5:-1])

reviews['display'] = np.where(reviews['category'].isin(['COUP DE CŒUR', 'À VOIR', 'On adore']), 'yes', 'no')


print("\nCOLLECTING WEEKS:")
date_list, name_list, week_list = [], [], []
for date, link in links.items():

    try:
        html = requests.get(link)
        soup = BeautifulSoup(html.content, 'html.parser')

        date_l, name_l, week_l = [], [], []

        weeks = soup.findAll(class_ = 'mcnBoxedTextBlock')

        for week in weeks:
            date_l.append(date)
            name_l.append(week.find("h3").text)
            week_l.append(str(week.find(class_="mcnTextContent").find("div")))

        date_list += date_l
        name_list += name_l
        week_list += week_l

    except:
        print('{} Failed'.format(date))

weeks = pd.DataFrame({
    'date': date_list,
    'name': name_list,
    'week': week_list,
}).sort_values('date', ascending=False).reset_index(drop=True)

weeks['week'] = weeks['week'].apply(lambda x: clean_up_week(x))


print("\nExporting")
json_export = {}
json_export['review'] = []
for i in range(reviews.shape[0]):
    temp_dict = {}
    for var in list(reviews):
        temp_dict[var] = reviews[var][i]
    json_export['review'].append(temp_dict)
with open('../website_cine/data/reviews.json', 'w') as f:
    json.dump(json_export, f)

json_export = {}
json_export['week'] = []
for i in range(weeks.shape[0]):
    temp_dict = {}
    for var in list(weeks):
        temp_dict[var] = weeks[var][i]
    json_export['week'].append(temp_dict)
with open('../website_cine/data/weeks.json', 'w') as f:
    json.dump(json_export, f)
