import time
import firebase_admin
from firebase_admin import credentials, firestore

from scraper_screenings import get_movies, movie_level_data_for_website, date_level_data_for_website
from scraper_newsletter import collecting_reviews_and_weeks, upload_data_in_database

def upload_movies(event, context):
    print("\n\nSCREENINGS SCRAPER:")
    print("\nFetching data...")
    movies = get_movies()
    movies_data = movie_level_data_for_website(movies, year_constraint=3) #keys: films ids; values: dicts
    dates_data = date_level_data_for_website(movies, year_constraint=3) #keys: dates; values: dicts{date:date, movies:list of movies}
    all_movie_dates_data = date_level_data_for_website(movies, year_constraint=0) #keys: dates; values: dicts{date:date, movies:list of movies}

    print("\nUploading to database...")
    cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    for date in dates_data.keys():
        db.collection(u'per_date').document(date).set(dates_data[date], merge=True)
        time.sleep(0.05)

    for date in all_movie_dates_data.keys():
        db.collection(u'all_movies_per_date').document(date).set(all_movie_dates_data[date], merge=True)
        time.sleep(0.05)

    for movie_id in movies_data.keys():
        db.collection(u'per_movie').document(movie_id).set(movies_data[movie_id])
        time.sleep(0.05)

    print("Done uploading screenings to database!")

def upload_newsletter(event, context):
    print("\n\nNEWSLETTER SCRAPER:")
    json_export_reviews, json_export_weeks, json_export_dates, json_export_cdc_without_images, json_export_curiosite_without_images  = collecting_reviews_and_weeks()

    if not firebase_admin._apps:
        cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    upload_data_in_database(db, json_export_reviews, "reviews")
    upload_data_in_database(db, json_export_weeks, "weeks")

    print("Pushing the list of dates.")
    ref = db.collection("reviews").document("all_dates")
    ref.set(json_export_dates, merge=True)

    print("Pushing the list of review without images.")
    ref = db.collection("reviews").document("all_coup_de_coeur")
    ref.set(json_export_cdc_without_images, merge=True)
    ref = db.collection("reviews").document("all_curiosite")
    ref.set(json_export_curiosite_without_images, merge=True)

    print("Done uploading newsletter to database!")
