from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time
import re
from typing import List, Optional
from datetime import datetime
import os
import json

import logging
import unicodedata
import backoff
import jmespath
from tqdm.auto import tqdm
import requests


nationalities = {
    'AD': ('andorran', 'andorrane'),
    'AE': ('émirien', 'émirienne'),
    'AF': ('afghan', 'afghane'),
    'AG': ('antiguayen', 'antiguayenne'),
    'AI': ('anguillais', 'anguillaise'),
    'AL': ('albanais', 'albanaise'),
    'AM': ('arménien', 'arménienne'),
    'AO': ('angolais', 'angolaise'),
    'AR': ('argentin', 'argentine'),
    'AS': ('samoan', 'samoane'),
    'AT': ('autrichien', 'autrichienne'),
    'AU': ('australien', 'australienne'),
    'AW': ('arubain', 'arubaine'),
    'AX': ('ålandais', 'ålandaise'),
    'AZ': ('azerbaïdjanais', 'azerbaïdjanaise'),
    'BA': ('bosnien', 'bosnienne'),
    'BB': ('barbadien', 'barbadienne'),
    'BD': ('bangladais', 'bangladaise'),
    'BE': ('belge', 'belge'),
    'BF': ('burkinabè', 'burkinabè'),
    'BG': ('bulgare', 'bulgare'),
    'BH': ('bahreïnien', 'bahreïnienne'),
    'BI': ('burundais', 'burundaise'),
    'BJ': ('béninois', 'béninoise'),
    'BM': ('bermudien', 'bermudienne'),
    'BN': ('brunéiens', 'brunéiennes'),
    'BO': ('bolivien', 'bolivienne'),
    'BR': ('brésilien', 'brésilienne'),
    'BS': ('bahamien', 'bahamienne'),
    'BT': ('bhoutanais', 'bhoutanaise'),
    'BW': ('botswanais', 'botswanaise'),
    'BY': ('biélorusse', 'biélorusse'),
    'BZ': ('bélizien', 'bélizienne'),
    'CA': ('canadien', 'canadienne'),
    'CD': ('congolais', 'congolaise'),
    'CF': ('centrafricain', 'centrafricaine'),
    'CG': ('congolais', 'congolaise'),
    'CH': ('suisse', 'suissesse'),
    'CI': ('ivoirien', 'ivoirienne'),
    'CK': ('cookien', 'cookienne'),
    'CL': ('chilien', 'chilienne'),
    'CM': ('camerounais', 'camerounaise'),
    'CN': ('chinois', 'chinoise'),
    'CO': ('colombien', 'colombienne'),
    'CR': ('costaricien', 'costaricienne'),
    'CU': ('cubain', 'cubaine'),
    'CV': ('cap-verdien', 'cap-verdienne'),
    'CY': ('chypriote', 'chypriote'),
    'CS': ('tchécoslovaque', 'tchécoslovaque'),
    'CZ': ('tchèque', 'tchèque'),
    'DE': ('allemand', 'allemande'),
    'DJ': ('djiboutien', 'djiboutienne'),
    'DK': ('danois', 'danoise'),
    'DM': ('dominiquais', 'dominiquaise'),
    'DO': ('dominicain', 'dominicaine'),
    'DZ': ('algérien', 'algérienne'),
    'EC': ('équatorien', 'équatorienne'),
    'EE': ('estonien', 'estonienne'),
    'EG': ('égyptien', 'égyptienne'),
    'EH': ('sahraoui', 'sahraouie'),
    'EL': ('grec', 'grecque'),
    'ER': ('érythréen', 'érythréenne'),
    'ES': ('espagnol', 'espagnole'),
    'ET': ('éthiopien', 'éthiopienne'),
    'FI': ('finlandais', 'finlandaise'),
    'FJ': ('fidjien', 'fidjienne'),
    'FK': ('malouin', 'malouine'),
    'FM': ('micronésien', 'micronésienne'),
    'FO': ('féroïen', 'féroïenne'),
    'FR': ('français', 'française'),
    'GA': ('gabonais', 'gabonaise'),
    'GB': ('britannique', 'britannique'),
    'GD': ('grenadin', 'grenadine'),
    'GE': ('géorgien', 'géorgienne'),
    'GH': ('ghanéen', 'ghanéenne'),
    'GI': ('gibraltarien', 'gibraltarienne'),
    'GL': ('groenlandais', 'groenlandaise'),
    'GM': ('gambien', 'gambienne'),
    'GN': ('guinéen', 'guinéenne'),
    'GQ': ('équatoguinéen', 'équatoguinéenne'),
    'GR': ('grec', 'grecque'),
    'GT': ('guatémaltèque', 'guatémaltèque'),
    'GU': ('guamien', 'guamienne'),
    'GW': ('bissaoguinéen', 'bissaoguinéenne'),
    'GY': ('guyanien', 'guyanienne'),
    'HK': ('hongkongais', 'hongkongaise'),
    'HN': ('hondurien', 'hondurienne'),
    'HR': ('croate', 'croate'),
    'HT': ('haïtien', 'haïtienne'),
    'HU': ('hongrois', 'hongroise'),
    'ID': ('indonésien', 'indonésienne'),
    'IE': ('irlandais', 'iirlandaise'),
    'IL': ('israélien', 'israélienne'),
    'IN': ('indien', 'indienne'),
    'IQ': ('iraquien', 'iraquienne'),
    'IR': ('iranien', 'iranienne'),
    'IS': ('islandais', 'islandaise'),
    'IT': ('italien', 'italienne'),
    'JM': ('jamaïcain', 'jamaïcaine'),
    'JO': ('jordanien', 'jordanienne'),
    'JP': ('japonais', 'japonaise'),
    'KE': ('kényan', 'kényane'),
    'KG': ('kirghize', 'kirghize'),
    'KH': ('cambodgien', 'cambodgienne'),
    'KI': ('kiribatien', 'kiribatienne'),
    'KM': ('comorien', 'comorienne'),
    'KN': ('christophien', 'christophienne'),
    'KP': ('nord-coréen', 'nord-coréenne'),
    'KR': ('sud-coréen', 'sud-coréenne'),
    'KW': ('koweïtien', 'koweïtienne'),
    'KY': ('caïmanais', 'caïmanaise'),
    'KZ': ('kazakh', 'kazakhe'),
    'LA': ('laotien', 'laotienne'),
    'LB': ('libanais', 'libanaise'),
    'LC': ('saint-lucien', 'saint-lucienne'),
    'LI': ('liechtensteinois', 'liechtensteinoise'),
    'LK': ('sri-lankais', 'sri-lankaise'),
    'LR': ('libérien', 'libérienne'),
    'LS': ('mosotho', 'mosotho'),
    'LT': ('lituanien', 'lituanienne'),
    'LU': ('luxembourgeois', 'luxembourgeoise'),
    'LV': ('letton', 'lettone'),
    'LY': ('libyen', 'libyenne'),
    'MA': ('marocain', 'marocaine'),
    'MC': ('monégasque', 'monégasque'),
    'MD': ('moldave', 'moldave'),
    'ME': ('monténégrin', 'monténégrine'),
    'MG': ('malgache', 'malgache'),
    'MH': ('marshallais', 'marshallaise'),
    'MK': ('macédonien', 'macédonienne'),
    'ML': ('malien', 'malienne'),
    'MM': ('birman', 'birmane'),
    'MN': ('mongol', 'mongole'),
    'MO': ('macanais', 'macanaise'),
    'MP': ('mariannais', 'mariannaise'),
    'MR': ('mauritanien', 'mauritanienne'),
    'MS': ('montserratien', 'montserratienne'),
    'MT': ('maltais', 'maltaise'),
    'MU': ('mauricien', 'mauricienne'),
    'MV': ('maldivien', 'maldivienne'),
    'MW': ('malawien', 'malawienne'),
    'MX': ('mexicain', 'mexicaine'),
    'MY': ('malaisien', 'malaisienne'),
    'MZ': ('mozambicain', 'mozambicaine'),
    'NA': ('namibien', 'namibienne'),
    'NE': ('nigérien', 'nigérienne'),
    'NG': ('nigérian', 'nigériane'),
    'NI': ('nicaraguayen', 'nicaraguayenne'),
    'NL': ('néerlandais', 'néerlandaise'),
    'NO': ('norvégien', 'norvégienne'),
    'NP': ('népalais', 'népalaise'),
    'NR': ('nauruan', 'nauruane'),
    'NU': ('niuéan', 'niuéane'),
    'NZ': ('néo-zélandais', 'néo-zélandaise'),
    'OM': ('omanais', 'omanaise'),
    'PA': ('panaméen', 'panaméenne'),
    'PE': ('péruvien', 'péruvienne'),
    'PG': ('papouasien', 'papouasienne'),
    'PH': ('philippin', 'philippine'),
    'PK': ('pakistanais', 'pakistanaise'),
    'PL': ('polonais', 'polonaise'),
    'PR': ('portoricain', 'portoricaine'),
    'PS': ('palestinien', 'palestinienne'),
    'PT': ('portugais', 'portugaise'),
    'PW': ('palaois', 'palaoise'),
    'PY': ('paraguayen', 'paraguayenne'),
    'QA': ('qatarien', 'qatarienne'),
    'RO': ('roumain', 'roumaine'),
    'RS': ('serbe', 'serbe'),
    'RU': ('russe', 'russe'),
    'RW': ('rwandais', 'rwandaise'),
    'SA': ('saoudien', 'saoudienne'),
    'SB': ('salomonais', 'salomonaise'),
    'SC': ('seychellois', 'seychelloise'),
    'SD': ('soudanais', 'soudanaise'),
    'SE': ('suédois', 'suédoise'),
    'SG': ('singapourien', 'singapourienne'),
    'SI': ('slovène', 'slovène'),
    'SK': ('slovaque', 'slovaque'),
    'SL': ('sierraléonais', 'sierraléonaise'),
    'SM': ('saint-marinais', 'saint-marinaise'),
    'SN': ('sénégalais', 'sénégalaise'),
    'SO': ('somalien', 'somalienne'),
    'SR': ('surinamais', 'surinamaise'),
    'SS': ('sud-soudanais', 'sud-soudanaise'),
    'ST': ('santoméen', 'santoméenne'),
    'SU': ('soviétique', 'soviétique'),
    'SV': ('salvadorien', 'salvadorienne'),
    'SY': ('syrien', 'syrienne'),
    'SZ': ('swazi', 'swazie'),
    'TC': ('émirats arabes unis', 'émirats arabes unis'),
    'TD': ('tchadien', 'tchadienne'),
    'TG': ('togolais', 'togolaise'),
    'TH': ('thaïlandais', 'thaïlandaise'),
    'TJ': ('tadjik', 'tadjike'),
    'TK': ('tokélaouen', 'tokélaouenne'),
    'TL': ('timorais', 'timoraise'),
    'TM': ('turkmène', 'turkmène'),
    'TN': ('tunisien', 'tunisienne'),
    'TO': ('tongan', 'tongane'),
    'TP': ('est-timorais', 'est-timoraise'),
    'TR': ('turc', 'turque'),
    'TT': ('trinidadien', 'trinidadienne'),
    'TV': ('tuvaluan', 'tuvaluane'),
    'TW': ('taïwanais', 'taïwanaise'),
    'TZ': ('tanzanien', 'tanzanienne'),
    'UA': ('ukrainien', 'ukrainienne'),
    'UG': ('ougandais', 'ougandaise'),
    'UK': ('britannique', 'britannique'),
    'US': ('américain', 'américaine'),
    'UY': ('uruguayen', 'uruguayenne'),
    'UZ': ('ouzbek', 'ouzbèke'),
    'VC': ('vincentais', 'vincentaise'),
    'VE': ('vénézuélien', 'vénézuélienne'),
    'VG': ('insulaires des îles vierges britanniques', 'insulaires des îles vierges britanniques'),
    'VI': ('insulaires des îles vierges', 'insulaires des îles vierges'),
    'VN': ('vietnamien', 'vietnamienne'),
    'VU': ('vanuatuan', 'vanuatuane'),
    'WS': ('samoan', 'samoane'),
    'XK': ('kosovar', 'kosovare'),
    'YE': ('yéménite', 'yéménite'),
    'YU': ('serbe', 'serbe'),
    'ZA': ('sud-africain', 'sud-africaine'),
    'ZM': ('zambien', 'zambienne'),
    'ZW': ('zimbabwéen', 'zimbabwéenne'),
}


countries = {
    'andorre': 'AD',
    'emirats arabes unis': 'AE',
    'afghanistan': 'AF',
    'antigua et barbuda': 'AG',
    'anguilla': 'AI',
    'albanie': 'AL',
    'curacao': 'AN',
    'angola': 'AO',
    'argentine': 'AR',
    'samoa americaines': 'AS',
    'autriche': 'AT',
    'australie': 'AU',
    'aruba': 'AW',
    'azerbaidjan': 'AZ',
    'bosnie-herzegovine': 'BA',
    'barbade': 'BB',
    'bangladesh': 'BD',
    'belgique': 'BE',
    'burkina faso': 'BF',
    'bulgarie': 'BG',
    'bahrein': 'BH',
    'burundi': 'BI',
    'benin': 'BJ',
    'bermudes': 'BM',
    'brunei': 'BN',
    'bolivie': 'BO',
    'bresil': 'BR',
    'bahamas': 'BS',
    'bhoutan': 'BT',
    'botswana': 'BW',
    'bielorussie': 'BY',
    'belize': 'BZ',
    'canada': 'CA',
    'congo rdc': 'CD',
    'republique centrafricaine': 'CF',
    'congo (brazzaville)': 'CG',
    'suisse': 'CH',
    'cote d\'ivoire': 'CI',
    'iles cook': 'CK',
    'chili': 'CL',
    'cameroun': 'CM',
    'chine': 'CN',
    'colombie': 'CO',
    'costa rica': 'CR',
    'cuba': 'CU',
    'cap vert': 'CV',
    'chypre': 'CY',
    'republique tcheque': 'CZ',
    'tchecoslovaquie': 'CS',
    'allemagne': 'DE',
    'allemagne de l\'ouest': 'DE',
    'allemagne de l\'est': 'DE',
    'djibouti': 'DJ',
    'danemark': 'DK',
    'dominique': 'DM',
    'republique dominicaine': 'DO',
    'algerie': 'DZ',
    'equateur': 'EC',
    'estonie': 'EE',
    'egypte': 'EG',
    'erythree': 'ER',
    'espagne': 'ES',
    'ethiopie': 'ET',
    'finlande': 'FI',
    'fidji': 'FJ',
    'iles malouines': 'FK',
    'micronesie': 'FM',
    'france': 'FR',
    'gabon': 'GA',
    'grande-bretagne': 'GB',  # modified based on allocine value, originally 'Royaume-Uni'
    'grenade': 'GD',
    'georgie': 'GE',
    'ghana': 'GH',
    'gibraltar': 'GI',
    'gambie': 'GM',
    'guinee': 'GN',
    'guinee equatoriale': 'GQ',
    'grece': 'GR',
    'guatemala': 'GT',
    'guam': 'GU',
    'guinee-bissau': 'GW',
    'guyana': 'GY',
    'hong kong': 'HK',
    'hong-kong': 'HK',
    'honduras': 'HN',
    'croatie': 'HR',
    'haiti': 'HT',
    'hongrie': 'HU',
    'indonesie': 'ID',
    'irlande': 'IE',
    'israel': 'IL',
    'inde': 'IN',
    'irak': 'IQ',
    'islande': 'IS',
    'italie': 'IT',
    'jamaique': 'JM',
    'jordanie': 'JO',
    'japon': 'JP',
    'kenya': 'KE',
    'kyrghyzstan': 'KG',
    'cambodge': 'KH',
    'kiribati': 'KI',
    'comores': 'KM',
    'saint-christophe-et-nieves': 'KN',
    'coree du sud': 'KR',  # modified based on allocine value, originally 'Coree, Republique de'
    'koweit': 'KW',
    'iles caimans': 'KY',
    'kazakhstan': 'KZ',
    'laos': 'LA',
    'liban': 'LB',
    'sainte-lucie': 'LC',
    'liechtenstein': 'LI',
    'sri lanka': 'LK',
    'liberia': 'LR',
    'lesotho': 'LS',
    'lituanie': 'LT',
    'luxembourg': 'LU',
    'lettonie': 'LV',
    'libye': 'LY',
    'maroc': 'MA',
    'monaco': 'MC',
    'moldavie': 'MD',
    'montenegro': 'ME',
    'madagascar': 'MG',
    'iles marshall': 'MH',
    'macedoine': 'MK',
    'mali': 'ML',
    'birmanie': 'MM',
    'mongolie': 'MN',
    'macao': 'MO',
    'iles mariannes du nord': 'MP',
    'mauritanie': 'MR',
    'montserrat': 'MS',
    'malte': 'MT',
    'maurice': 'MU',
    'maldives': 'MV',
    'malawi': 'MW',
    'mexique': 'MX',
    'malaisie': 'MY',
    'mozambique': 'MZ',
    'namibie': 'NA',
    'niger': 'NE',
    'nigeria': 'NG',
    'nicaragua': 'NI',
    'pays-bas': 'NL',
    'norvege': 'NO',
    'nepal': 'NP',
    'nauru': 'NR',
    'nioue': 'NU',
    'nouvelle-zelande': 'NZ',
    'oman': 'OM',
    'panama': 'PA',
    'perou': 'PE',
    'papouasie-nouvelle-guinee': 'PG',
    'philippines': 'PH',
    'pakistan': 'PK',
    'pologne': 'PL',
    'porto rico': 'PR',
    'autorite palestinienne': 'PS',
    'portugal': 'PT',
    'palaos': 'PW',
    'paraguay': 'PY',
    'qatar': 'QA',
    'roumanie': 'RO',
    'russie': 'RU',
    'rwanda': 'RW',
    'arabie saoudite': 'SA',
    'iles salomon': 'SB',
    'soudan': 'SD',
    'suede': 'SE',
    'singapour': 'SG',
    'slovenie': 'SI',
    'slovaquie': 'SK',
    'sierra leone': 'SL',
    'senegal': 'SN',
    'somalie': 'SO',
    'suriname': 'SR',
    'sao tome-et-principe': 'ST',
    'el salvador': 'SV',
    'saint-martin': 'SX',
    'syrie': 'SY',
    'iles turques-et-caiques': 'TC',
    'tchad': 'TD',
    'togo': 'TG',
    'thailande': 'TH',
    'tadjikistan': 'TJ',
    'turkmenistan': 'TM',
    'tunisie': 'TN',
    'tonga': 'TO',
    'timor oriental': 'TP',
    'turquie': 'TR',
    'trinite-et-tobago': 'TT',
    'tuvalu': 'TV',
    'taiwan': 'TW',
    'tanzanie': 'TZ',
    'ukraine': 'UA',
    'ouganda': 'UG',
    'u.r.s.s.': 'SU',
    'u.s.a.': 'US',  # modified based on allocine value, originally 'etats-unis'
    'uruguay': 'UY',
    'ouzbekistan': 'UZ',
    'saint-vincent-et-les grenadines': 'VC',
    'venezuela': 'VE',
    'iles vierges (britanniques)': 'VG',
    'iles vierges': 'VI',
    'vietnam': 'VN',
    'vanuatu': 'VU',
    'samoa occidentales': 'WS',
    'kosovo': 'XK',
    'yemen': 'YE',
    'serbie': 'YU',
    'afrique du sud': 'ZA',
    'zambie': 'ZM',
    'zimbabwe': 'ZW',
}

DEFAULT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
BASE_URL = 'http://api.allocine.fr/rest/v3'
PARTNER_KEY = '000042532791'

logger = logging.getLogger(__name__)


# === Models ===
@dataclass
class Movie:
    movie_id: int
    title: str
    original_title: str
    rating: Optional[float]
    duration: Optional[timedelta]
    genres: str
    countries: List[str]
    directors: str
    actors: str
    synopsis: str
    year: int

    @property
    def duration_str(self):
        if self.duration is not None:
            return _strfdelta(self.duration, '{hours:02d}h{minutes:02d}')
        else:
            return 'HH:MM'

    @property
    def duration_short_str(self) -> str:
        if self.duration is not None:
            return _strfdelta(self.duration, '{hours:d}h{minutes:02d}')
        else:
            return 'NA'

    @property
    def rating_str(self):
        return '{0:.1f}'.format(self.rating) if self.rating else ''

    @property
    def nationalities(self):
        """ Return the nationality tuples, from the movie countries.
            Example: if self.countries = ['France'] => [('français', 'française')]
        """
        if self.countries:
            nationality_tuples = []
            for country_name in self.countries:
                normalized_country_name = _strip_accents(country_name).lower()
                country_code = nationalities.countries.get(normalized_country_name)

                if country_code is not None:
                    nationality_tuples.append(nationalities.nationalities[country_code])
                else:
                    logger.warning(f'Country {country_name!r} not found in nationalities')
                    nationality_tuples.append((f'de {country_name}', f'de {country_name}'))
            return nationality_tuples
        else:
            return None

    def __str__(self):
        return f'{self.title} [{self.movie_id}] ({self.duration_str})'

    def __eq__(self, other):
        return (self.movie_id) == (other.movie_id)

    def __hash__(self):
        """ This function allows us
        to do a set(list_of_Movie_objects) """
        return hash(self.movie_id)


@dataclass
class MovieVersion(Movie):
    language: str
    screen_format: str

    @property
    def version(self):
        version = 'VF' if self.language == 'Français' else 'VOST'
        if self.screen_format != 'Numérique':
            version += f' {self.screen_format}'
        return version

    def get_movie(self):
        return Movie(
            movie_id=self.movie_id,
            title=self.title,
            rating=self.rating,
            duration=self.duration,
            original_title=self.original_title,
            year=self.year,
            genres=self.genres,
            countries=self.countries,
            directors=self.directors,
            actors=self.actors,
            synopsis=self.synopsis,
        )

    def __str__(self):
        movie_str = super().__str__()
        return f'{movie_str} ({self.version})'

    def __eq__(self, other):
        return (self.movie_id, self.version) == (other.movie_id, other.version)

    def __hash__(self):
        """ This function allows us
        to do a set(list_of_MovieVersion_objects) """
        return hash((self.movie_id, self.version))


@dataclass
class Schedule:
    date_time: datetime

    @property
    def date(self) -> date:
        return self.date_time.date()

    @property
    def hour(self) -> datetime.time:
        return self.date_time.time()

    @property
    def hour_str(self) -> str:
        return self.date_time.strftime('%H:%M')

    @property
    def hour_short_str(self) -> str:
        return get_hour_short_str(self.hour)

    @property
    def date_str(self) -> date:
        return self.date_time.strftime('%d/%m/%Y %H:%M')

    @property
    def day_str(self) -> str:
        return day_str(self.date)

    @property
    def short_day_str(self) -> str:
        return short_day_str(self.date)


def get_hour_short_str(hour: datetime.time) -> str:
    # Ex: 9h, 11h, 23h30
    # Minus in '%-H' removes the leading 0
    return hour.strftime('%-Hh%M').replace('h00', 'h')


@dataclass
class Showtime(Schedule):
    movie: MovieVersion

    def __str__(self):
        return f'{self.date_str} : {self.movie}'


def day_str(date: date) -> str:
    return to_french_weekday(date.weekday())


def to_french_weekday(weekday: int) -> str:
    DAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    return DAYS[weekday]


def get_french_month(month_number: int) -> str:
    MONTHS = [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ]
    return MONTHS[month_number-1]


def to_french_short_weekday(weekday: int) -> str:
    return to_french_weekday(weekday)[:3]


def short_day_str(date: date) -> str:
    return day_str(date)[:3]


@dataclass
class Theater:
    theater_id: str
    name: str
    showtimes: List[Showtime]
    address: str
    zipcode: str
    city: str

    @property
    def address_str(self):
        address_str = f'{self.address}, ' if self.address else ''
        address_str += f'{self.zipcode} {self.city}'
        return address_str

    def get_showtimes_of_a_movie(self, movie_version: MovieVersion, date: date = None):
        movie_showtimes = [showtime for showtime in self.showtimes
                           if showtime.movie == movie_version]
        if date:
            return [showtime for showtime in movie_showtimes
                    if showtime.date == date]
        else:
            return movie_showtimes

    def get_showtimes_of_a_day(self, date: date):
        return get_showtimes_of_a_day(showtimes=self.showtimes, date=date)

    def get_movies_available_for_a_day(self, date: date):
        """ Returns a list of movies available on a specified day """
        movies = [showtime.movie for showtime in self.get_showtimes_of_a_day(date)]
        return list(set(movies))

    def get_showtimes_per_movie_version(self):
        movies = {}
        for showtime in self.showtimes:
            if movies.get(showtime.movie) is None:
                movies[showtime.movie] = []
            movies[showtime.movie].append(showtime)
        return movies

    def get_showtimes_per_movie(self):
        movies = {}
        for showtime in self.showtimes:
            movie = showtime.movie.get_movie()  # Without language nor screen_format
            if movies.get(movie) is None:
                movies[movie] = []
            movies[movie].append(showtime)
        return movies

    def get_program_per_movie(self):
        program_per_movie = {}
        for movie, showtimes in self.get_showtimes_per_movie().items():
            program_per_movie[movie] = build_program_str(showtimes=showtimes)
        return program_per_movie

    def filter_showtimes(self, date_min: date = None, date_max: date = None):
        if date_min:
            self.showtimes = [s for s in self.showtimes if s.date >= date_min]
        if date_max:
            self.showtimes = [s for s in self.showtimes if s.date <= date_max]

    def __eq__(self, other):
        return (self.theater_id) == (other.theater_id)

    def __hash__(self):
        """ This function allows us to do a set(list_of_Theaters_objects) """
        return hash(self.theater_id)


# == Utils ==
def get_available_dates(showtimes: List[Showtime]):
    dates = [s.date for s in showtimes]
    return sorted(list(set(dates)))


def group_showtimes_per_schedule(showtimes: List[Showtime]):
    showtimes_per_date = {}
    available_dates = get_available_dates(showtimes=showtimes)
    for available_date in available_dates:
        showtimes_per_date[available_date] = get_showtimes_of_a_day(showtimes=showtimes, date=available_date)

    grouped_showtimes = {}
    for available_date in available_dates:
        hours = [s.hour_short_str for s in showtimes_per_date[available_date]]
        hours_str = ', '.join(hours)
        if grouped_showtimes.get(hours_str) is None:
            grouped_showtimes[hours_str] = []
        grouped_showtimes[hours_str].append(available_date)
    return grouped_showtimes


def build_program_str(showtimes: List[Showtime]):
    schedules = [Schedule(s.date_time) for s in showtimes]
    return build_weekly_schedule_str(schedules)


def check_schedules_within_week(schedule_list: List[Schedule]) -> bool:
    schedule_dates = [s.date for s in schedule_list]
    min_date = min(schedule_dates)
    max_date = max(schedule_dates)
    delta = (max_date - min_date)
    if delta >= timedelta(days=7):
        raise ValueError(
            'Schedule list contains more days than the typical movie week')
    # Check that the week is not from Mon/Tue to Wed/Thu/Fri/Sat/Sun
    # because a typical week is from Wed to Tue
    # but we need to handle the case of a schedule_list with only a few day
    # ex: Wed, Mon = OK ; Tue = OK ; Mon, Wed : NOK
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    if delta > timedelta(days=0):
        if (min_date.weekday() == MONDAY and max_date.weekday() >= WEDNESDAY) \
           or (min_date.weekday() == TUESDAY):
            raise ValueError(
                'Schedule list should not start before wednesday or end after tuesday')

    return True


def create_weekdays_str(dates: List[date]) -> str:
    """
        Returns a compact string from a list of dates.
        Examples:
            - [0,1] -> 'Lun, Mar'
            - [0,1,2,3,4] -> 'sf Sam, Dim'
            - [0,1,2,3,4,5,6] -> ''  # Everyday is empty string
            - [0,2] -> 'Mer, Lun'  # And not 'Lun, Mer' because we sort chrologically
    """
    FULL_WEEK = range(0, 7)
    unique_dates = sorted(list(set(dates)))
    week_days = [d.weekday() for d in unique_dates]

    if len(unique_dates) == 7:
        return ''
    elif len(unique_dates) <= 4:
        return ', '.join([to_french_short_weekday(d) for d in week_days])
    else:
        missing_days = list(set(week_days).symmetric_difference(FULL_WEEK))
        return 'sf {}'.format(', '.join([to_french_short_weekday(d) for d in missing_days]))


def __get_time_weight_in_list(d: dict) -> timedelta:
    """ Returns the minimum time weight from the time list contained in the dict values
        ex: {'key': [time(hour=12), time(hour=9)]} => timedelta(hour=9)
    """
    weights = [__get_time_weight(t) for t in d[1]]
    return min(weights)


def __get_time_weight(t: time) -> timedelta:
    """ Return a timedelta taking into account night time.
        Basically, it allows to sort a list of times 18h>23h>0h30
        and not 0h30>18h>23h
    """
    _NIGHT_TIME = [time(hour=0), time(hour=5)]
    delta = timedelta(hours=t.hour, minutes=t.minute)
    if t >= min(_NIGHT_TIME) and t <= max(_NIGHT_TIME):
        delta += timedelta(days=1)
    return delta


def build_weekly_schedule_str(schedule_list: List[Schedule]) -> str:
    check_schedules_within_week(schedule_list)

    _hours_hashmap = {}  # ex: {16h: [Lun, Mar], 17h: [Lun], 17h30: [Lun]}
    _grouped_date_hashmap = {}  # ex: {[Lun]: [16h, 17h30], [Lun, Mar]: [17h]}

    for s in schedule_list:

        if _hours_hashmap.get(s.hour) is None:
            _hours_hashmap[s.hour] = []
        _hours_hashmap[s.hour].append(s.date)

    for hour, grouped_dates in _hours_hashmap.items():
        grouped_dates_str = create_weekdays_str(grouped_dates)
        if _grouped_date_hashmap.get(grouped_dates_str) is None:
            _grouped_date_hashmap[grouped_dates_str] = []
        _grouped_date_hashmap[grouped_dates_str].append(hour)

    # Then sort it chronologically
    for grouped_dates_str, hours in _grouped_date_hashmap.items():
        # Sort the hours inside
        hours = list(set(hours))
        hours.sort()
        _grouped_date_hashmap[grouped_dates_str] = hours

    grouped_date_hashmap = OrderedDict()
    _grouped_date_hashmap = sorted(_grouped_date_hashmap.items(), key=__get_time_weight_in_list)
    grouped_date_hashmap = OrderedDict(_grouped_date_hashmap)

    hours_hashmap = OrderedDict()
    for t in sorted(_hours_hashmap.keys(), key=__get_time_weight):
        hours_hashmap[t] = _hours_hashmap.get(t)

    different_showtimes = len(grouped_date_hashmap)

    # True if at least one schedule is available everyday
    some_schedules_available_everyday = grouped_date_hashmap.get('') is not None

    weekly_schedule = ''

    if some_schedules_available_everyday:
        for hour, grouped_dates in hours_hashmap.items():
            hour_str = get_hour_short_str(hour)
            grouped_dates_str = create_weekdays_str(grouped_dates)
            if grouped_dates_str:
                weekly_schedule += f'{hour_str} ({grouped_dates_str}), '
            else:  # Available everyday
                weekly_schedule += f'{hour_str}, '
    else:
        for grouped_dates, hours in grouped_date_hashmap.items():
            hours_str = ', '.join([get_hour_short_str(h) for h in hours])
            if different_showtimes == 1:
                weekly_schedule += f'{grouped_dates} {hours_str}, '
            else:
                if some_schedules_available_everyday:
                    weekly_schedule += f'{hours_str} ({grouped_dates}), '
                else:
                    weekly_schedule += f'{grouped_dates} {hours_str}; '

    if weekly_schedule:
        weekly_schedule = weekly_schedule[:-2]  # Remove trailing comma
    return weekly_schedule


def get_showtimes_of_a_day(showtimes: List[Showtime], *, date: date):
    return [showtime for showtime in showtimes
            if showtime.date == date]


# === Main class ===
class Allocine:
    def __init__(self, base_url=BASE_URL):
        self.__client = Client(base_url=base_url)
        self.__movie_store = {}  # Dict to store the movie info (and avoid useless requests)

    def get_theater(self, theater_id: str):
        ret = self.__client.get_showtimelist_by_theater_id(theater_id=theater_id)
        if jmespath.search('feed.totalResults', ret) == 0:
            raise ValueError(f'Theater not found. Is theater id {theater_id!r} correct?')

        theaters = self.__get_theaters_from_raw_showtimelist(raw_showtimelist=ret)
        if len(theaters) != 1:
            raise ValueError('Expecting 1 theater but received {}'.format(len(theaters)))

        return theaters[0]

    def __get_theaters_from_raw_showtimelist(self, raw_showtimelist: dict, distance_max_inclusive: int = 0):
        theaters = []
        for theater_showtime in jmespath.search('feed.theaterShowtimes', raw_showtimelist):
            raw_theater = jmespath.search('place.theater', theater_showtime)

            if raw_theater.get('distance') is not None:
                # distance is not present when theater ids were used for search
                if raw_theater.get('distance') > distance_max_inclusive:
                    # Skip theaters that are above the max distance specified
                    continue

            raw_showtimes = jmespath.search('movieShowtimes', theater_showtime)
            showtimes = self.__parse_showtimes(raw_showtimes=raw_showtimes)
            theater = Theater(
                theater_id=raw_theater.get('code'),
                name=raw_theater.get('name'),
                address=raw_theater.get('address'),
                zipcode=raw_theater.get('postalCode'),
                city=raw_theater.get('city'),
                showtimes=showtimes
            )
            theaters.append(theater)
        return theaters

    def search_theaters(self, geocode: int):
        theaters = []
        page = 1
        while True:
            ret = self.__client.get_showtimelist_from_geocode(geocode=geocode, page=page)
            total_results = jmespath.search('feed.totalResults', ret)
            if total_results == 0:
                raise ValueError(f'Theater not found. Is geocode {geocode!r} correct?')

            theaters_to_parse = jmespath.search('feed.theaterShowtimes', ret)
            if theaters_to_parse:
                theaters += self.__get_theaters_from_raw_showtimelist(
                    raw_showtimelist=ret,
                    distance_max_inclusive=0
                )
                page += 1
            else:
                break

        return theaters

    def __parse_showtimes(self, raw_showtimes: dict):
        showtimes = []
        for s in raw_showtimes:
            raw_movie = jmespath.search('onShow.movie', s)
            language = jmespath.search('version."$"', s)
            screen_format = jmespath.search('screenFormat."$"', s)
            duration = raw_movie.get('runtime')
            duration_obj = timedelta(seconds=duration) if duration else None

            rating = jmespath.search('statistics.userRating', raw_movie)
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = None

            movie_id = raw_movie.get('code')
            movie_info = self.get_movie_info(movie_id)
            countries = jmespath.search('nationality[]."$"', movie_info)
            year = movie_info.get('productionYear')
            if year:
                year = int(year)
            movie = MovieVersion(
                movie_id=movie_id,
                title=raw_movie.get('title'),
                rating=rating,
                language=language,
                screen_format=screen_format,
                synopsis=_clean_synopsis(movie_info.get('synopsis')),
                original_title=movie_info.get('originalTitle'),
                year=year,
                countries=countries,
                genres=', '.join(jmespath.search('genre[]."$"', movie_info)),
                directors=jmespath.search('castingShort.directors', movie_info),
                actors=jmespath.search('castingShort.actors', movie_info),
                duration=duration_obj)
            for showtimes_of_day in s.get('scr') or []:
                day = showtimes_of_day.get('d')
                for one_showtime in showtimes_of_day.get('t'):
                    datetime_str = '{}T{}:00'.format(day, one_showtime.get('$'))
                    datetime_obj = _str_datetime_to_datetime_obj(datetime_str)
                    showtime = Showtime(
                        date_time=datetime_obj,
                        movie=movie,
                    )
                    showtimes.append(showtime)
        return showtimes

    def get_movie_info(self, movie_id: int):
        movie_info = self.__movie_store.get(movie_id)
        if movie_info is None:
            movie_info = self.__client.get_movie_info_by_id(movie_id).get('movie')
            self.__movie_store[movie_id] = movie_info
        return movie_info


# === Client to execute requests with Allociné APIs ===
class SingletonMeta(type):
    _instance = None

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance


class Error503(Exception):
    pass


class Client(metaclass=SingletonMeta):
    """ Client to process the requests with allocine APIs.
    This is a singleton to avoid the creation of a new session for every theater.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; \
                                   Intel Mac OS X 10.14; rv:63.0) \
                                   Gecko/20100101 Firefox/63.0',
                    }
        self.session = requests.session()
        self.session.headers.update(headers)

    @backoff.on_exception(backoff.expo, Error503, max_tries=5, max_time=30)
    def _get(self, url: str, expected_status: int = 200, *args, **kwargs):
        ret = self.session.get(url, *args, **kwargs)
        if ret.status_code != expected_status:
            if ret.status_code == 503:
                raise Error503
            raise ValueError('{!r} : expected status {}, received {}'.format(
                url, expected_status, ret.status_code))
        return ret.json()

    def get_showtimelist_by_theater_id(self, theater_id: str, page: int = 1, count: int = 10):
        url = (
                f'{self.base_url}/showtimelist?partner={PARTNER_KEY}&format=json'
                f'&theaters={theater_id}&page={page}&count={count}'
        )
        return self._get(url=url)

    def get_theater_info_by_id(self, theater_id: str):
        url = f'{self.base_url}/theater?partner={PARTNER_KEY}&format=json&code={theater_id}'
        return self._get(url=url)

    def get_showtimelist_from_geocode(self, geocode: int, page: int = 1, count: int = 10):
        url = (
                f'{self.base_url}/showtimelist?partner={PARTNER_KEY}&format=json'
                f'&geocode={geocode}&page={page}&count={count}'
        )
        return self._get(url=url)

    def get_movie_info_by_id(self, movie_id: int):
        url = (
                f'{self.base_url}/movie?partner={PARTNER_KEY}&format=json&code={movie_id}'
        )
        return self._get(url=url)


def _strfdelta(tdelta, fmt):
    """ Format a timedelta object """
    # Thanks to https://stackoverflow.com/questions/8906926
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def _str_datetime_to_datetime_obj(datetime_str, date_format=DEFAULT_DATE_FORMAT):
    return datetime.strptime(datetime_str, date_format)


def _cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def _clean_synopsis(raw_synopsis):
    if raw_synopsis is None:
        return None

    synopsis = _cleanhtml(raw_synopsis)  # Remove HTML tags (ex: <span>)
    synopsis = synopsis.replace('\xa0', ' ')
    return unicodedata.normalize("NFKD", synopsis)


def _strip_accents(s):
    # https://stackoverflow.com/a/518232/8748757
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

#######################
#end of T Ducret's code
#######################

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
    if name == "Le Louxor - Palais du cinéma":
        name = "Le Louxor"
    name = name.strip()
    return name

def good_movie(movie):
    if movie['directors']==None:
        return False
    if movie['title']=="Wallace & Gromit : Cœurs à modeler":
        return False
    else:
        return True

######################
#ALLOCINE SCRAPER#####
######################
def allocine_scraper():
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
            
    return movies, theater_info

######################
#PREP DATA FOR WEBSITE
######################
def prep_data_for_website():
    todays_date = datetime.today()
    last_year = todays_date.year - 4
    current_path = os.getcwd()
    data_path = os.path.join(current_path, 'data')
    date = os.listdir(data_path)
    date.sort()
    date = date[-1].split('_')[0] #get the date from the latest file

    print("Fetching data collected on {}".format(date))
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