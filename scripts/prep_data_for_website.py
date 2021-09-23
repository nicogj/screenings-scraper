import datetime
import numpy as np
import itertools
import re
import os
import time
import glob
from collections import OrderedDict
import json

from utils.utils import load_obj, save_obj, clean_theater_name, good_movie, transform_zipcode, get_last_name

last_year = 2017

current_path = os.getcwd()
data_path = os.path.join(current_path, 'data')
date = os.listdir(data_path)
date.sort()
date = date[-1].split('_')[0] #get the date from the latest file

print("Fetching data collected on {}".format(date))
date_name = os.path.join(data_path, date)
classic_movies = load_obj('{}_movies.pkl'.format(date_name))
theaters = load_obj('{}_theaters.pkl'.format(date_name))

classic_movies = {
    k: v for k, v in classic_movies.items() if v['year'] <= last_year
}
classic_movies = {
    k: v for k, v in classic_movies.items() if len(v['showtimes'].keys()) > 0
}
classic_movies = {
    k: v for k, v in classic_movies.items() if good_movie(v)
}

classic_movies = {k: v for k, v in sorted(classic_movies.items(), key=lambda item: item[1]['year'])}
for movie in classic_movies.keys():
    classic_movies[movie]['showtimes'] = {
        k: classic_movies[movie]['showtimes'][k] for k in sorted(classic_movies[movie]['showtimes'])
    }
    for showdate in classic_movies[movie]['showtimes'].keys():
        for theater in classic_movies[movie]['showtimes'][showdate].keys():
            classic_movies[movie]['showtimes'][showdate][theater] = sorted(
                classic_movies[movie]['showtimes'][showdate][theater]
            )

movie_list = []
for movie_id in classic_movies.keys():
    for showtime in classic_movies[movie_id]['showtimes']:
        movie = {}
        movie['title'] = classic_movies[movie_id]['title']
        movie['original_title'] = classic_movies[movie_id]['original_title']
        movie['directors'] = classic_movies[movie_id]['directors']
        movie['last_name_directors'] = get_last_name(classic_movies[movie_id]['directors'])
        movie['year'] = classic_movies[movie_id]['year']
        movie['date'] = [showtime.year, showtime.month, showtime.day]
        movie['id'] = movie_id
        movie['showtimes_theater'] = dict()
        for theater in classic_movies[movie_id]['showtimes'][showtime].keys():
            dict_theater_name = '{} ({})'.format(clean_theater_name(theaters[theater]['name']), \
                transform_zipcode(theaters[theater]['zipcode']))
            movie['showtimes_theater'][dict_theater_name] = \
                [elem.hour + elem.minute/60 for elem in classic_movies[movie_id]['showtimes'][showtime][theater]]

        showtimes = []
        for theater in classic_movies[movie_id]['showtimes'][showtime].keys():
            showtimes.append('{} ({}): {}'.format(
                clean_theater_name(theaters[theater]['name']),
                transform_zipcode(theaters[theater]['zipcode']),
                ', '.join([
                    str(elem.hour)+'h'+str(elem.minute).zfill(2)
                    for elem in classic_movies[movie_id]['showtimes'][showtime][theater]
                ])
            ))
        movie['showtimes'] = '<br>'.join(showtimes)

        movie_list.append(movie)
classic_movies = {}
classic_movies['movies'] = movie_list

with open('../website_cine/classic_movies.json', 'w') as f:
    json.dump(classic_movies, f)
