from datetime import datetime
from tqdm.auto import tqdm
import time
from allocine import Allocine
from utils import get_theater_codes, good_movie, encode_movie, add_movie_feats, add_theater_feats

def theater_scraper(theater_code):

    allocine = Allocine()
    try_nb = 0
    while try_nb < 5:
        try:
            theater_data = allocine.get_theater(theater_code)
            break
        except:
            try_nb += 1
            print("Trying again for {}".format(theater_code))
            time.sleep(5)
    if try_nb==5:
        print("Could not fetch theater {}".format(theater_code))
        print("Please check https://www.allocine.fr/seance/salle_gen_csalle={}.html to see if we're missing out.".format(theater_code))
        theater_data = None

    return theater_data

def get_movies():

    theaters = get_theater_codes()
    movies = {}

    for theater in tqdm(theaters):

        theater_data = theater_scraper(theater)

        if theater_data is None:
            continue

        for showtime in theater_data.showtimes:

            movie_id = encode_movie(showtime.movie.title, showtime.movie.year, showtime.movie.directors)
            date = str(showtime.date.year) + "_" + str(showtime.date.month).zfill(2) + "_" + str(showtime.date.day).zfill(2)
            theater_id = theater # this might change as we leave Allocine

            if movie_id not in movies:
                movies[movie_id] = {}
                movies[movie_id]['allocine_id'] = str(showtime.movie.movie_id)
                for key in ['title', 'original_title', 'year', 'directors', 'language', 'countries']:
                    movies[movie_id][key] = vars(showtime.movie)[key]
                movies[movie_id]['duration'] = None if showtime.movie.duration is None else showtime.movie.duration.seconds
                movies[movie_id]['screenings'] = {}

            else:
                if movies[movie_id]['title'] != showtime.movie.title:
                    print("*** Encoding error on title {} (encoded as {}) ***".format(showtime.movie.title, movie_id))

            if date not in movies[movie_id]['screenings']:
                movies[movie_id]['screenings'][date] = {}

            if theater_id not in movies[movie_id]['screenings'][date]:
                movies[movie_id]['screenings'][date][theater_id] = {}
                for key in ['name', 'address', 'city', 'zipcode']:
                    movies[movie_id]['screenings'][date][theater_id][key] = vars(theater_data)[key]
                movies[movie_id]['screenings'][date][theater_id]['showtimes'] = []

            movies[movie_id]['screenings'][date][theater_id]['showtimes'].append(showtime.date_time.hour+showtime.date_time.minute/60)
            movies[movie_id]['screenings'][date][theater_id]['showtimes'] = list(set(
                movies[movie_id]['screenings'][date][theater_id]['showtimes']
            ))

    return movies

def subset_to_classic_movies(movies):
    last_year = datetime.today().year - 4
    classic_movies = movies.copy()
    classic_movies = {
        k: v for k, v in classic_movies.items() if v['directors'] != None
    }
    classic_movies = {
        k: v for k, v in classic_movies.items() if v['year'] != None
    }
    classic_movies = {
        k: v for k, v in classic_movies.items() if v['year'] <= last_year
    }
    classic_movies = {
        k: v for k, v in classic_movies.items() if len(v['screenings'].keys()) > 0
    }
    classic_movies = {
        k: v for k, v in classic_movies.items() if good_movie(v)
    }
    return classic_movies

######################
#PREP DATA FOR WEBSITE
######################

def movie_level_data_for_website(movies):

    classic_movies = subset_to_classic_movies(movies)
    by_movie = classic_movies.copy()

    # Additional variables:
    for movie in by_movie.keys():
        by_movie[movie] = add_movie_feats(by_movie[movie])
        for date in by_movie[movie]['screenings'].keys():
            for theater in by_movie[movie]['screenings'][date].keys():
                by_movie[movie]['screenings'][date][theater] = add_theater_feats(by_movie[movie]['screenings'][date][theater])

    return by_movie


def date_level_data_for_website(movies):

    classic_movies = subset_to_classic_movies(movies)
    by_date = {}
    for movie in classic_movies.keys():
        for date in classic_movies[movie]['screenings'].keys():
            if date not in by_date:
                by_date[date] = {}
                by_date[date]['date'] = date
                by_date[date]['movies'] = []
            by_date[date]['movies'].append(classic_movies[movie].copy())
            by_date[date]['movies'][-1]['showtimes_theater'] = classic_movies[movie]['screenings'][date].copy()
            del by_date[date]['movies'][-1]['screenings']

    # Additional variables:
    for date in by_date.keys():
        for movie in by_date[date]['movies']:
            movie = add_movie_feats(movie)
            for theater in movie['showtimes_theater']:
                movie['showtimes_theater'][theater] = add_theater_feats(movie['showtimes_theater'][theater])

    return by_date
