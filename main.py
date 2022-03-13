import time
import firebase_admin
from firebase_admin import credentials, firestore

from scheduling_movies.screenings_scraper import \
    get_movies, movie_level_data_for_website, date_level_data_for_website
from scheduling_reviews.newsletter_scraper import \
    collecting_reviews_and_weeks, upload_data_in_database, \
    upload_data_in_database, upload_the_list_of_movies, upload_the_list_of_dates


def upload_movies(event, context):
    print("Creating the data!")
    movies = get_movies()
    #keys: films ids; values: dicts
    movies_data = movie_level_data_for_website(movies)
    #keys: dates; values: dicts{date:date, movies:list of movies}
    dates_data = date_level_data_for_website(movies)
    
    print("")
    print("Uploading to the database!")
    cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    for date in dates_data.keys():
        db.collection(u'data_per_date').document(date).set(dates_data[date])
        time.sleep(0.05)

    for movie_id in movies_data.keys():
        db.collection(u'data_per_movie').document(movie_id).set(movies_data[movie_id])
        time.sleep(0.05)


def upload_newsletter(event, context):
    json_export_reviews, json_export_weeks, json_export_dates  = collecting_reviews_and_weeks()
    if not firebase_admin._apps:
        cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    upload_data_in_database(db, json_export_reviews, "reviews")
    upload_data_in_database(db, json_export_weeks, "weeks")
    upload_the_list_of_movies(db, json_export_reviews)
    upload_the_list_of_dates(db, json_export_dates)


upload_movies(None, None)