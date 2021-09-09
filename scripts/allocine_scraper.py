from allocine import Allocine
import datetime
from IPython.display import display, Markdown
from tqdm.auto import tqdm
import numpy as np
import itertools
import re
import os
import time
import pickle

from utils.utils import get_theater_codes, save_obj

if __name__ == '__main__':

    allocine = Allocine()
    theater_codes = get_theater_codes()

    movies = {}
    theater_info = {}

    for theater_code in tqdm(theater_codes):

        try:
            theater = allocine.get_theater(theater_code)
        except:
            print("Could not fetch theater {}".format(theater_code))
            continue

        theater_info[theater_code] = {}
        theater_info[theater_code]['name'] = theater.name
        theater_info[theater_code]['address'] = theater.address
        theater_info[theater_code]['city'] = theater.city
        theater_info[theater_code]['zipcode'] = theater.zipcode

        for showtime in theater.showtimes:

            if showtime.movie.movie_id not in movies:
                movies[showtime.movie.movie_id] = {}
                movies[showtime.movie.movie_id]['title'] = showtime.movie.title
                movies[showtime.movie.movie_id]['original_title'] = showtime.movie.original_title
                movies[showtime.movie.movie_id]['duration'] = showtime.movie.duration
                movies[showtime.movie.movie_id]['year'] = showtime.movie.year
                movies[showtime.movie.movie_id]['directors'] = showtime.movie.directors
                movies[showtime.movie.movie_id]['language'] = showtime.movie.language
                movies[showtime.movie.movie_id]['screen_format'] = showtime.movie.screen_format
                movies[showtime.movie.movie_id]['id'] = showtime.movie.movie_id
                movies[showtime.movie.movie_id]['showtimes'] = {}

            if showtime.date not in movies[showtime.movie.movie_id]['showtimes']:
                movies[showtime.movie.movie_id]['showtimes'][showtime.date] = {}
            if theater_code not in movies[showtime.movie.movie_id]['showtimes'][showtime.date]:
                movies[showtime.movie.movie_id]['showtimes'][showtime.date][theater_code] = []

            movies[showtime.movie.movie_id]['showtimes'][showtime.date][theater_code].append(showtime.date_time)
            movies[showtime.movie.movie_id]['showtimes'][showtime.date][theater_code] = list(
                set(movies[showtime.movie.movie_id]['showtimes'][showtime.date][theater_code])
            )

        save_obj(theater_info, 'data/{}{}{}_theaters.pkl'.format(
            datetime.datetime.today().year,
            str(datetime.datetime.today().month).zfill(2),
            str(datetime.datetime.today().day).zfill(2)
        ))
        save_obj(movies, 'data/{}{}{}_movies.pkl'.format(
            datetime.datetime.today().year,
            str(datetime.datetime.today().month).zfill(2),
            str(datetime.datetime.today().day).zfill(2)
        ))
