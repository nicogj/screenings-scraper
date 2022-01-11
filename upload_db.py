import firebase_admin
import json
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

#docs = db.collection(u'allocine_movies2021_12_28').stream()
#for doc in docs:
#    print(f'{doc.id} => {doc.to_dict()}')
#sys.exit()


def delete_collection(coll_ref, batch_size):
    docs = db.collection(coll_ref).stream()
    deleted = 0
    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


with open('classic_movies.json') as file:
    movies = json.load(file)["movies"]
    for movie in movies:
        #dates are year_month_day
        date = '_'.join([str(int) for int in movie['date']])
        collection_name = u'allocine_movies_' + date
        #delete_collection(collection_name, 5)
        ref = db.collection(collection_name).document(str(movie.get("id", "none" )))
        ref.set(movie, merge=True)