import re

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

def get_sort_name(name):
    name = name.split(",")[0].upper().strip() # Only first director
    sort_name = name.split(" ")[-1] + ", " + " ".join(name.split(" ")[:-1]) # Get last word of name

    # Include particles
    if sort_name.split(" ")[-2:] = ["DE", "LA"]:
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
