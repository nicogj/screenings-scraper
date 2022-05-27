import re
import re
import unidecode
import nltk
import time
nltk.download('stopwords')
from nltk.corpus import stopwords
import firebase_admin
from firebase_admin import credentials, firestore
from google_trans_new import google_translator
detector = google_translator()

stopwords_list = stopwords.words('english')+stopwords.words('french')
stopwords_list = [elem for elem in stopwords_list if elem not in ["suis"]]

def get_theater_codes():

    theater_codes = [
        'C0015', # Christine Cinéma Club (Christine 21)
        'C0061', # Cinéma Studio 28
        'C0071', # Écoles Cinéma Club (Écoles 21)
        'C0076', # Cinéma du Panthéon
        'C0108', # Elysées Lincoln
        'C0153', # Cinéma Chaplin Denfert
        'P7517', # 7 Batignolles
        'W7515', # Cinéma Chaplin Saint Lambert
        'W7517', # Club de l'Etoile
        'W7519', # CGR Paris Lilas
        'C0007', # Gaumont Champs-Elysées - Marignan
        'C0020', # Filmothèque du Quartier Latin
        'C0024', # Gaumont Les Fauvettes
        'C0037', # Gaumont Alésia
        'C0042', # Epée de Bois
        'C0116', # Gaumont Aquaboulevard
        'C0117', # Espace Saint-Michel
        'C0147', # Escurial
        'C0161', # Gaumont Convention
        'W7513', # Fondation Jerome Seydoux - Pathé
        'C0004', # Le Cinéma des Cinéastes
        'C0009', # Le Balzac
        'C0023', # Le Brady Cinema & Théâtre
        'C0054', # L'Arlequin
        'C0065', # Le Grand Rex
        'C0073', # Le Champo - Espace Jacques Tati
        'C0134', # L'Archipel - PARIS CINE
        'C0158', # Gaumont Parnasse
        'C1559', # La Cinémathèque française
        'W7510', # Le Louxor - Palais du cinéma
        'C0005', # L'Entrepôt
        'C0012', # Les Cinq Caumartin
        'C0013', # Luminor Hôtel de Ville
        'C0040', # MK2 Bastille (côté Fg St Antoine)
        'C0050', # MK2 Beaubourg
        'C0089', # Max Linder Panorama
        'C0095', # Les 3 Luxembourg
        'C0120', # Majestic Passy
        'C0139', # Majestic Bastille
        'C0140', # MK2 Bastille (côté Beaumarchais)
        'C0003', # MK2 Quai de Seine
        'C0041', # Nouvel Odéon
        'C0092', # MK2 Odéon (Côté St Michel)
        'C0097', # MK2 Odéon (Côté St Germain)
        'C0099', # MK2 Parnasse
        'C0144', # MK2 Nation
        'C0192', # MK2 Gambetta
        'C1621', # MK2 Quai de Loire
        'C2954', # MK2 Bibliothèque
        'W7502', # Pathé Beaugrenelle
        'C0016', # Studio Galande
        'C0025', # Sept Parnassiens
        'C0060', # Pathé Opéra Premier
        'C0074', # Reflet Medicis
        'C0083', # Studio des Ursulines
        'C0096', # Silencio Pop-up
        'C0100', # Saint-André des Arts
        'C0179', # Pathé Wepler
        'C6336', # Publicis Cinémas
        'W7520', # Pathé La Villette
        'C0010', # UGC Normandie
        'C0026', # UGC Ciné Cité Bercy
        'C0127', # Centre Pompidou
        'C0102', # UGC Danton
        'C0103', # UGC Montparnasse
        'C0104', # UGC Odéon
        'C0146', # UGC Lyon Bastille
        'C0150', # UGC Gobelins
        'C0159', # UGC Ciné Cité Les Halles
        'C0175', # UGC Maillot
        'W7509', # UGC Ciné Cité Paris 19
        'C0105', # UGC Rotonde
        'C0126', # UGC Opéra
        'B0116', # Cinéma Le Mélies
        'B0104', # Cin'Hoche
        'B0047', # Ciné 104
        'B0101', # LE STUDIO
        'B0123', # ESPACE 1789
        'C0072', # LE GRAND ACTION
        'B0127', # La Pleiade Cachan
        'B0119', # Le Trianon Romainville
        'B0040', # Cin'Hoche Sartrouville
        'B0107', # Ciné Malraux
        'B0148', # Le Vincennes
        'B0167', # Les Toiles Saint-Gratien
        'B0215', # Cinémassy
        'B0122', # L'écran Saint Denis
        'B0003', # Etoile Cosmos Chelles
        'B0110', # L'Etoile La Courneuve
        'B0073', # Le Select Antony
        'C0119', # Le Forum des Images
    ]

    return theater_codes

def transform_zipcode(code):
    if str(code)[:2] == '75':
        arr = int(code) - 75000
        if arr == 1:
            arr_name = str(arr) + "er"
        else:
            arr_name = str(arr) + "ème"
        if arr in [1, 2, 3, 4]:
            arr_cat = "Paris 1, 2, 3, 4"
        elif arr in [5, 6, 7]:
            arr_cat = "Paris 5, 6, 7"
        elif arr in [8, 17]:
            arr_cat = "Paris 8 & 17"
        elif arr in [9, 10, 18, 19]:
            arr_cat = "Paris 9, 10, 18, 19"
        elif arr in [11, 12, 20]:
            arr_cat = "Paris 11, 12, 20"
        elif arr in [13, 14]:
            arr_cat = "Paris 13 & 14"
        elif arr in [15, 16]:
            arr_cat = "Paris 15 & 16"
        else:
            arr_cat = "Paris {}".format(arr)
        if arr in [1, 2, 3, 4, 8, 9, 10, 11, 12, 16, 17, 18, 19, 20]:
            arr_cat2 = 'rd'
        elif arr in [5, 6, 7, 13, 14, 15]:
            arr_cat2 = 'rg'
        return arr_name, arr_cat, arr_cat2
    else:
        return str(code), "Extramuros", 'em'

def clean_theater_name(name):
    if name == "Christine Cinéma Club (Christine 21)":
        name = "Christine Cinéma Club"
    if name == "Écoles Cinéma Club (Écoles 21)":
        name = "Écoles Cinéma Club"
    if name == "Gaumont Champs-Elysées - Marignan":
        name = "Gaumont Champs-Elysées"
    if name == "Fondation Jerome Seydoux - Pathé":
        name = "Fondation Jerome Seydoux"
    if name == "Le Champo - Espace Jacques Tati":
        name = "Le Champo"
    if name == "L'Archipel - PARIS CINE":
        name = "L'Archipel"
    if name == "Le Brady Cinema & Théâtre":
        name = "Le Brady"
    if name == "Le Louxor - Palais du cinéma":
        name = "Le Louxor"
    if name == "Centre Georges-Pompidou":
        name = "Centre Pompidou"
    name = name.strip()
    return name

def clean_movie_title(name):
    if name == "As I Was Moving Ahead Occasionnaly I Saw Brief Glimpses of Beauty":
        name = "As I Was Moving Ahead Occasionally I Saw Brief Glimpses of Beauty"
    name = name.strip()
    return name

def get_sort_name(name):
    name = name.split(",")[0].upper().strip() # Only first director
    sort_name = name.split(" ")[-1] + ", " + " ".join(name.split(" ")[:-1]) # Get last word of name

    # Include particles
    if sort_name.split(" ")[-2:] == ["DE", "LA"]:
        sort_name = "DE LA" + " ".join(sort_name[:-2])
    if sort_name.split(" ")[-1] in ["LE", "LA", "DE"]:
        sort_name = sort_name[-1] + " ".join(sort_name[:-1])

    # Exceptions
    if name in [elem.upper() for elem in ["WONG KAR-WAI", "Hou Hsiao-hsien", "Jia Zhangke"]]:
        sort_name = name

    if name in "Jose Leitao de Barros".upper():
        sort_name = "Leitao de Barros, Jose".upper()

    return sort_name

def good_movie(movie):
    children_movies = [
        "Wallace & Gromit : Cœurs à modeler",
        "Oups ! J’ai raté l’arche…",
        "Les Trois brigands",
        "Le Chant de la Mer",
        "Clochette et le secret des fées",
        "Lilla Anna"
    ]
    if movie['directors']==None:
        return False
    if movie['title'] in children_movies:
        return False
    else:
        return True

def reduce_movie_title(movie_title):

    movie_title = movie_title.lower()

    # Remove special characters
    movie_title = unidecode.unidecode(movie_title)
    movie_title = re.sub('[^A-z0-9]', ' ', movie_title)
    movie_title = re.sub('\s+', ' ', movie_title)
    movie_title = movie_title.strip()

    # Remove stop words
    if len(movie_title.split(' ')) > 3:
        # lang = detector.detect(movie_title)[1] # THIS STEP IS TAKING TOO LONG
        movie_title = movie_title.split(' ')
        try:
            # non_stop_words = [word for word in movie_title if word not in stopwords.words(lang)]
            non_stop_words = [word for word in movie_title if word not in stopwords_list]
        except:
            non_stop_words = movie_title
        if len(non_stop_words) > 0:
            movie_title = ' '.join(non_stop_words)
        else:
            movie_title = ' '.join(movie_title)

    return movie_title

def encode_movie(movie_title, movie_year, movie_directors):

    movie_title = clean_movie_title(movie_title)
    movie_title = reduce_movie_title(movie_title)
    movie_title = '-'.join(movie_title.split(' '))

    movie_year = str(movie_year)

    id = movie_title + '-' + movie_year

    return id

def add_movie_feats(movie):
    movie['director_sort_name'] = get_sort_name(movie['directors'])
    movie['id'] = encode_movie(movie['title'], movie['year'], movie['directors'])
    return movie

def add_theater_feats(theater):
    theater['clean_name'] = clean_theater_name(theater['name'])
    theater['zipcode_clean'], theater['location_1'], theater['location_2'] = transform_zipcode(theater['zipcode'])
    return theater

def clean_up_string(string):
    string = string.replace('\xa0', ' ')
    string = string.strip()

    for char in [':', ';', '!', '?', '«', '»']:
        string = re.sub(r'\s\{}'.format(char), '&nbsp;{}'.format(char), string)
    for char in ['«']:
        string = re.sub(r'\{}\s'.format(char), '{}&nbsp;'.format(char), string)

    return string.strip()



def download_collection_and_process(collection_name):
    cred = credentials.Certificate('website-cine-e77fb4ab2924.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    def get_list_movies(db, category):
        docs = db.collection(collection_name).where(u'category', u'==', category).stream()
        list_reviews_without_images_per_date = dict()
        list_reviews_without_images_per_id = dict()
        for doc in docs:
            elem_aux = doc.to_dict().copy()
            del elem_aux["image"]
            del elem_aux["image_file"]
            del elem_aux["review"]
            del elem_aux["showtime"]
            del elem_aux["time"]
            if not "title" in elem_aux:
                elem_aux["title"] = elem_aux["movie_name"]
            if not "directors" in elem_aux:
                elem_aux["directors"] = elem_aux["movie_directors"]
            if not "year" in elem_aux:
                elem_aux["year"] = elem_aux["movie_year"]
            elem_aux["id"] = encode_movie(elem_aux["title"], \
                elem_aux["year"], elem_aux["directors"])

            list_reviews_without_images_per_date[str(elem_aux["date"])] = elem_aux
            list_reviews_without_images_per_id[elem_aux["id"]] = elem_aux
        return list_reviews_without_images_per_date, list_reviews_without_images_per_id

    cdc_without_images_date, cdc_without_images_id = get_list_movies(db, "COUP DE CŒUR")
    curiosite_without_images_date, curiosite_without_images_id = get_list_movies(db, "ON EST CURIEUX")

    print("Pushing all the reviews in the document 'all_reviews' (without images).")
    ref = db.collection("reviews").document("all_coup_de_coeur")
    ref.set(cdc_without_images_date, merge=True)
    ref = db.collection("reviews").document("all_curiosite")
    ref.set(curiosite_without_images_date, merge=True)

    print("Pushing the movies with reviews in the Per movie collection.")
    for movie_id in cdc_without_images_id.keys():
        db.collection(u'per_movie').document(movie_id).set(cdc_without_images_id[movie_id], merge=True)
        time.sleep(0.05)
    for movie_id in curiosite_without_images_id.keys():
        db.collection(u'per_movie').document(movie_id).set(curiosite_without_images_id[movie_id], merge=True)
        time.sleep(0.05)

#download_collection_and_process("reviews")
