import datetime
from typing import List, Dict
from django.conf import settings
from django.db import connections
import os
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}


def download_poster(program_id, movie_id):
    base_urls = [
        'https://images-s.kinorium.com/movie/400/',
        'https://en-images.kinorium.com/movie/400/',
        'https://en-images-s.kinorium.com/movie/400/',
        'https://ru-images.kinorium.com/movie/400/',
        'https://ru-images-s.kinorium.com/movie/400/',
    ]

    os.makedirs(settings.STATIC_BANNERS, exist_ok=True)
    image_filename = os.path.join(settings.STATIC_BANNERS, f'{program_id}.jpg')

    if os.path.exists(image_filename):
        return 'success'

    for base_url in base_urls:
        poster_url = f'{base_url}{movie_id}.jpg'
        try:
            response = requests.get(poster_url, headers=headers, stream=True, timeout=10)
            print(image_filename, poster_url)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    continue

                file_size = int(response.headers.get('content-length', 0))
                if not 1024*2 < file_size < 1024*1024*10:
                    continue

                with open(image_filename, 'wb') as f:
                    for chunk in response.iter_content(8192):
                        f.write(chunk)
                    insert_into_db(program_id)
                    print('poster downloaded')
                    return 'success'

        except (requests.RequestException, OSError) as e:
            print(e)
    return 'error'


def poster_parser(query: Dict):
    program_name = query['title'].replace('ё', 'е')
    program_name = program_name.replace('`', '')
    program_name = program_name.replace('’', '')
    program_name = program_name.replace(' ', '%20')
    program_name = program_name.split('сезон')[0]
    program_name = program_name.split('серия')[0]
    program_name = program_name[:35]
    program_year = query['year']

    search_url = f'https://ru.kinorium.com/search/?q={program_name}%20{program_year}'
    print('search_url', search_url)
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_list = soup.find('div', {'class': 'movieList'})
        print(movie_list)
        if movie_list:
            movies = []
            for item in movie_list.find_all('div', {'class': 'item'}):
                title_tag = item.find('h3', {'class': 'search-page__item-title'})
                movie_id = title_tag.get('data-id') if title_tag else None

                title_link = item.find('a', {'class': 'search-page__item-title-text'})
                title = title_link.get_text(strip=True) if title_link else None

                year_tag = item.find('small', {'class': 'cut_text'})
                production_year = year_tag.get_text(strip=True).split(',')[0] if year_tag else None

                extro_info = item.find('div', {'class': 'search-page__extro-info'})
                if extro_info:
                    genre_div = extro_info.find('div', {'class': 'search-page__genre-list'})
                    if genre_div:
                        genre_div.extract()
                    country = extro_info.get_text(strip=True)
                else:
                    country = None

                if movie_id and title and production_year:
                    movies.append({
                        'program_id': query['program_id'],
                        'data-id': movie_id,
                        'title': title,
                        'year': production_year,
                        'country': country,
                    })
            return movies


def split_countries(countries_str):
    if not countries_str or not countries_str.strip():
        return []
    return [c.strip() for c in countries_str.replace("'", "").split(',')]


def calculate_year_score(query_year, movie_year):
    try:
        query_year = int(query_year.strip().split('-')[0].split('–')[0].split('—')[0])
        movie_year = int(movie_year.strip().split('-')[0].split('–')[0].split('—')[0])
    except Exception as e:
        print(e)
        return 0
    year_diff = abs(query_year - movie_year)
    return 1 if year_diff <= 1 else 0


def normalize_similarity(value: float) -> float:
    return max(0, min(1, value / 100))


def calculate_match_score(query: Dict, movie: Dict) -> tuple:
    weights = {
        'title': 0.55,
        'year': 0.25,
        'country': 0.2
    }
    # Сравнение названия (нечеткое сравнение)
    title_similarity = fuzz.token_set_ratio(query['title'].lower(), movie['title'].lower())
    title_score = normalize_similarity(title_similarity) * weights['title']

    # Сравнение года (точное сравнение с небольшим допуском)
    year_score = calculate_year_score(query['year'], movie['year']) * weights['year']

    # Сравнение страны (нечеткое сравнение)
    query_country = split_countries(query['country'])
    movie_country = split_countries(movie['country'])
    country_intersection = set(query_country) & set(movie_country)
    country_similarity = len(country_intersection)/max(len(query_country), len(movie_country))
    country_score = country_similarity * weights['country']

    return title_score, year_score, country_score

def search(query: Dict, threshold: float = 0.7) -> Dict:
    image_filename = os.path.join(settings.STATIC_BANNERS, f"{query['program_id']}.jpg")
    if os.path.exists(image_filename):
        return {}
    results = []
    movie_list = poster_parser(query)
    print(movie_list)
    if not movie_list:
        return {}
    for movie in movie_list:
        title_score, year_score, country_score = calculate_match_score(query, movie)
        total_score = title_score + year_score + country_score
        if total_score >= threshold:
            results.append({
                'movie': movie,
                'score': total_score,
                'details': {
                    'title_score': title_score,
                    'year_score': year_score,
                    'country_score': country_score
                }
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    if results: return results[0]
    return []


def check_db(program_id):
    image_filename = os.path.join(settings.STATIC_BANNERS, f'{program_id}.jpg')
    with connections['planner'].cursor() as cursor:
        query = f'SELECT [exists] FROM [planner].[dbo].[banner_list] WHERE [program_id] = {program_id}'
        cursor.execute(query)
        if cursor.fetchone() and os.path.exists(image_filename):
            return True
    return False

def insert_into_db(program_id):
    try:
        with connections['planner'].cursor() as cursor:
            query = f'''
            INSERT INTO [planner].[dbo].[banner_list]
            ([program_id], [date_of_addition], [exists]) VALUES 
            (%s, GETDATE(), %s)
            '''
            cursor.execute(query, (program_id, True))
    except Exception as e:
        print('not added', e)