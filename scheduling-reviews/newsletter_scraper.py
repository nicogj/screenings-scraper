import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
import urllib
import numpy as np
import time
import sys
import base64
import math
import io
from PIL import Image
from io import BytesIO
from datetime import datetime
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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

def collecting_reviews_and_weeks():
    base_url = 'https://us6.campaign-archive.com/home/?u=00a9245e71d3375ef4542a588&id=3270cdb251'

    html = requests.get(base_url)
    soup = BeautifulSoup(html.content, 'html.parser')

    links = {}
    for elem in soup.find_all(class_ = 'campaign'):
        links[elem.text[6:10]+"-"+elem.text[3:5]+"-"+elem.text[:2]] = elem.find('a').get('href')

    print("\nCOLLECTING REVIEWS:")
    over1MB = 0
    date_list, year_list, month_list, time_list, image_list, image_file_list, category_list, movie_list, review_list, \
        showtime_list, id_list = [], [], [], [], [], [], [], [], [], [], []
    for date, link in links.items():

        try:
            html = requests.get(link)
            soup = BeautifulSoup(html.content, 'html.parser')

            date_l, year_l, month_l, time_l, image_l, image_file_l, category_l, movie_l, review_l, showtime_l, id_l = [], [], [], [], [], [], [], [], [], [], []

            i=1
            texts = soup.findAll(class_ = 'mcnImageCardBlock')
            for text in texts:
                datelist = date.split("-")
                year, month = datelist[0], datelist[1]
                dt = datetime.strptime(date, '%Y-%m-%d')
                year_l.append(year)
                month_l.append(month)
                date_l.append(date)
                time_l.append(str(int(time.mktime(dt.timetuple()))))
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
                img_bytes = urllib.request.urlopen(image_url).read()
                img = base64.b64encode(img_bytes)
                if sys.getsizeof(img)>908487:
                    ratio = math.sqrt(sys.getsizeof(img)/1000000)+0.05
                    img = Image.open(io.BytesIO(img_bytes))
                    img = img.resize((int(img.size[0]/ratio), int(img.size[1]/ratio)))
                    im_file = BytesIO()
                    img.save(im_file, format="PNG")
                    img = im_file.getvalue()
                    img = base64.b64encode(img)

                img = img.decode('utf-8')
                image_file_l.append(img)
                i += 1

            date_list += date_l
            month_list += month_l
            year_list += year_l
            time_list += time_l
            image_list += image_l
            image_file_list += image_file_l
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
        'year': year_list,
        'month': month_list,
        'time': time_list,
        'category': category_list,
        'movie': movie_list,
        'review': review_list,
        'showtime': showtime_list,
        'image': image_list,
        'image_file': image_file_list
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
    reviews.loc[
        (reviews['movie']=="Hotel by the River, Hong Sang-Soo\u00a0(2018)")&(reviews['date']=="2022-02-16"), 'review'
    ] = "Un po\u00e8te qui sent la mort s\u2019approcher a donn\u00e9 rendez-vous \u00e0 ses fils dans un h\u00f4tel au bord d\u2019une rivi\u00e8re. Les retrouvailles sont difficiles&nbsp;: au sens propre (ils ne parviennent pas \u00e0 se retrouver dans le restaurant de l\u2019h\u00f4tel) comme au figur\u00e9 (il y a un je-ne-sais-quoi de distendu dans les relations entre le p\u00e8re et ses fils). Comme souvent chez Hong Sang-Soo (ou comme souvent, tout court), les langues se d\u00e9lient autour d\u2019un verre. L\u2019alcool est ce moteur schizophr\u00e9nique de la discussion qui r\u00e9v\u00e8le autant qu\u2019il fait oublier. Certaines choses s\u2019\u00e9chappent, bien d\u2019autres s\u2019effacent\u2026 Pendant ce temps dans le m\u00eame h\u00f4tel, une jeune femme, accompagn\u00e9e d\u2019une amie, pleure la fin de son couple. L\u2019\u00e9crivain partage un moment avec elles, leur r\u00e9cite un po\u00e8me qui les apaise. Mais l\u2019art n\u2019est pas un moyen de r\u00e9demption. Au mieux, il permet de saisir l\u2019inexorable fuite du temps et les regrets qui en d\u00e9coulent. Hong Sang-Soo nous le prouve ici mieux que quiconque."

    reviews['movie_name'] = reviews['movie'].apply(lambda x: ','.join(x.split(',')[:-1]))
    reviews['movie_directors'] = reviews['movie'].apply(lambda x: re.sub('\(.+\)', '', x.split(',')[-1]).strip())
    reviews['movie_year'] = reviews['movie'].apply(lambda x: x.split(',')[-1][-5:-1])
    reviews['display'] = np.where(reviews['category'].isin(['COUP DE CŒUR', 'À VOIR', 'On adore']), 'yes', 'no')


    print("\nCOLLECTING WEEKS:")
    date_list, year_list, month_list, time_list, name_list, week_list = [], [], [], [], [], []
    for date, link in links.items():

        try:
            html = requests.get(link)
            soup = BeautifulSoup(html.content, 'html.parser')
            date_l, name_l, week_l, year_l, month_l, time_l = [], [], [], [], [], []
            weeks = soup.findAll(class_ = 'mcnBoxedTextBlock')

            for week in weeks:
                datelist = date.split("-")
                year, month = datelist[0], datelist[1]
                dt = datetime.strptime(date, '%Y-%m-%d')
                year_l.append(year)
                month_l.append(month)
                time_l.append(str(int(time.mktime(dt.timetuple()))))
                date_l.append(date)
                name_l.append(week.find("h3").text)
                week_l.append(str(week.find(class_="mcnTextContent").find("div")))

            year_list += year_l
            month_list += month_l
            time_list += time_l
            date_list += date_l
            name_list += name_l
            week_list += week_l

        except:
            print('{} Failed'.format(date))

    weeks = pd.DataFrame({
        'year': year_list,
        'month': month_list,
        'time': time_list,
        'date': date_list,
        'name': name_list,
        'week': week_list,
    }).sort_values('date', ascending=False).reset_index(drop=True)

    weeks['week'] = weeks['week'].apply(lambda x: clean_up_week(x))


    print("\nExporting")
    json_export_reviews = {}
    json_export_reviews['reviews'] = []
    for i in range(reviews.shape[0]):
        temp_dict = {}
        for var in list(reviews):
            temp_dict[var] = reviews[var][i]
        json_export_reviews['reviews'].append(temp_dict)
    
    json_export_weeks = {}
    json_export_weeks['weeks'] = []
    for i in range(weeks.shape[0]):
        temp_dict = {}
        for var in list(weeks):
            temp_dict[var] = weeks[var][i]
        json_export_weeks['weeks'].append(temp_dict)
    
    return json_export_reviews, json_export_weeks

def upload_data_in_database(db, data, key):
    print("")
    print("Uploading to the database", key)
    data = data[key]
    last_date = sorted([movie["date"] for movie in data])[-1]
    for movie in data:
        if last_date==movie["date"]:
            if key=="reviews":
                doc_name = movie["date"] + "_" + movie["category"]
            else:
                doc_name = movie["date"]
            print("Pushing in DB!", doc_name)
            ref = db.collection(key).document(doc_name)
            ref.set(movie, merge=True)
        time.sleep(0.05)

def upload_the_list_of_movies(db, data):
    print("Pushing in DB the list of movies")
    movies = dict([(movie["movie_name"], movie["category"]) for movie in data["reviews"] \
        if movie["category"]=="COUP DE CŒUR"])
    ref = db.collection("reviews").document("all_movies")
    ref.set(movies, merge=True)

def main(event, context):
    json_export_reviews, json_export_weeks = collecting_reviews_and_weeks()
    if not firebase_admin._apps:
        cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    upload_data_in_database(db, json_export_reviews, "reviews")
    upload_data_in_database(db, json_export_weeks, "weeks")
    upload_the_list_of_movies(db, json_export_reviews)

main(None, None)