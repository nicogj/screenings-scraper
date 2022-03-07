import firebase_admin
from firebase_admin import credentials, firestore

def delete_some_collections():
    cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    listss = [] # Add list of collections here
    for coll_ref in listss:
        delete_collection(coll_ref, batch_size=50)


def delete_collection(coll_ref, batch_size):
    docs = db.collection(coll_ref).stream()
    deleted = 0
    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

def upload_data_in_database():
    #Use a service account
    print("")
    print("Uploading to the database!")

    cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    with open('classic_movies.json') as file:
        movies = json.load(file)

        for date in tqdm(movies.keys()):
            collection_name = u'movies'
            ref = db.collection(collection_name).document(date)
            ref.set({u'date': date}, merge=True)
            ref.update({u'movies': movies[date]})
            time.sleep(0.05)
