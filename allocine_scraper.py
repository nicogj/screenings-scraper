from allocine import Allocine
from datetime import datetime
from tqdm.auto import tqdm
import os
import json
import pickle
import time

def transform_zipcode(code):
    if str(code)[:2] == '75':
        arr = int(code) - 75000
        if arr == 1:
            arr = str(arr) + "er"
        else:
            arr = str(arr) + "ème"
        return arr
    else:
        return str(code)

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
    ]

    return theater_codes

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

######################
#ALLOCINE SCRAPER#####
######################
def save_obj(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

def allocine_scraper():
    allocine = Allocine()
    theater_codes = get_theater_codes()

    movies = {}
    theater_info = {}

    for theater_code in tqdm(theater_codes):
        try_nb = 1
        while try_nb < 5:
            try:
                theater = allocine.get_theater(theater_code)
                break
            except:
                try_nb += 1
                print("Trying again for {}".format(theater_code))
                time.sleep(5)
        if try_nb==5:
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
                if showtime.movie.year==None:
                    showtime.movie.year=datetime.today().year
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
        datetime.today().year,
        str(datetime.today().month).zfill(2),
        str(datetime.today().day).zfill(2)
    ))
    save_obj(movies, 'data/{}{}{}_movies.pkl'.format(
        datetime.today().year,
        str(datetime.today().month).zfill(2),
        str(datetime.today().day).zfill(2)
    ))

    return movies, theater_info

######################
#PREP DATA FOR WEBSITE
######################
def prep_data_for_website():

    last_year = datetime.today().year - 4

    classic_movies, theaters = allocine_scraper()

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

    with open('./classic_movies.json', 'w') as f:
        json.dump(classic_movies, f)

prep_data_for_website()
