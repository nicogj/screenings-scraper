import pickle
import time
import firebase_admin
from firebase_admin import credentials, firestore

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import logging
import re
from typing import List, Optional
import unicodedata

import backoff
import jmespath
import requests

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



######################
#SCRAPER UTILS########
######################

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
        return arr_name, arr_cat
    else:
        return str(code), "Extramuros"

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

    return name.split(" ")[-1] + ", " + " ".join(name.split(" ")[:-1])


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

            movie_id = showtime.movie.movie_id
            date = str(showtime.date.year) + "_" + str(showtime.date.month).zfill(2) + "_" + str(showtime.date.day).zfill(2)
            theater_id = theater # this might change as we leave Allocine

            if movie_id not in movies:
                movies[movie_id] = {}
                var = 'year'
                for key in ['title', 'original_title', 'year', 'directors', 'language']:
                    movies[movie_id][key] = vars(showtime.movie)[key]
                movies[movie_id]['duration'] = None if showtime.movie.duration is None else showtime.movie.duration.seconds
                movies[movie_id]['screenings'] = {}

            if date not in movies[movie_id]['screenings']:
                movies[movie_id]['screenings'][date] = {}

            if theater_id not in movies[movie_id]['screenings'][date]:
                movies[movie_id]['screenings'][date][theater_id] = {}
                for key in ['name', 'address', 'city', 'zipcode']:
                    movies[movie_id]['screenings'][date][theater_id][key] = vars(theater_data)[key]
                movies[movie_id]['screenings'][date][theater_id]['showtimes'] = []

            movies[movie_id]['screenings'][date][theater_id]['showtimes'].append(showtime.date_time.hour+showtime.date_time.minute/60)
            movies[movie_id]['screenings'][date][theater_id]['showtimes'] = list(set(
                tuple(i) for i in movies[movie_id]['screenings'][date][theater_id]['showtimes']
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

def add_movie_feats(movie):
    movie['director_sort_name'] = get_sort_name(movie['directors'])
    return movie

def add_theater_feats(theater):
    theater['clean_name'] = clean_theater_name(theater['name'])
    theater['zipcode_clean'], theater['location_1'], theater['location_2'] = transform_zipcode(theater['zipcode'])
    return theater

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


##################
####UPDATE DB#####
##################

def main(event, context):
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
        # ref = db.collection(u'dates_data').document(date)
        # ref.set({u'date': date}, merge=True)
        # ref.update({u'movies': movies[date]})
        time.sleep(0.05)

    for movie_id in movies_data.keys():
        db.collection(u'data_per_movie').document(movie_id).set(movies_data[movie_id])
        time.sleep(0.05)