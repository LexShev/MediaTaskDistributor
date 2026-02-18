import re

import requests
from bs4 import BeautifulSoup
# from rapidfuzz import fuzz


search_query = 'простоквашино'
search_url = f'https://www.kinopoisk.ru/index.php?kp_query={search_query}'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}


def search_movie_info(results):
    movies = []
    if results is None:
        print("Результаты поиска отсутствуют")
        return []

    for movie_container in results.find_all('div', {'class': 'element'}):
        movie_info = {
            'kinopoisk_id': None,
            'title': None,
            'original_title': None,
            'year': None,
            'material_type': None,
            'duration': None,
            'country': None,
            'director': {},
            'genre': [],
            'actors': [],
            'url': None,
        }

        info = movie_container.find('div', {'class': 'info'})
        if info:
            movie = info.find('p', {'class': 'name'})
            if movie:
                movie_link = movie.find('a')
                if movie_link:
                    movie_info['title'] = movie_link.text
                    year_container = movie.find('span', {'class': 'year'})
                    if year_container:
                        movie_info['year'] = year_container.text
                    kinopoisk_id = movie_link.get('data-id')
                    movie_info['kinopoisk_id'] = kinopoisk_id
                    movie_info['poster_url'] = f'https://www.kinopoisk.ru//images/sm_film/{kinopoisk_id}.jpg'
                    movie_info['material_type'] = movie_link.get('data-type')
                    movie_info['url'] = movie_link.get('data-url')
            gray_spans = info.find_all('span', {'class': 'gray'})
            if gray_spans:
                for span in gray_spans:
                    span_text = span.text.strip()
                    if 'мин' in span_text or re.search(r'[A-Za-z]', span_text):

                        # Ищем длительность
                        duration_match = re.search(r'(\d+)\s*мин', span_text)
                        duration = duration_match.group(0) if duration_match else None
                        if duration:
                            movie_info['duration'] = duration.strip(' мин')

                        # Если есть длительность, удаляем её из текста для получения оригинального названия
                        if duration:
                            original_title = span_text.replace(duration, '').strip(' ,')
                        else:
                            original_title = span_text.strip()

                        movie_info['original_title'] = original_title

                    director = span.find('i', {'class': 'director'})
                    if director:
                        director_container = director.find('a', {'class': 'lined'})
                        if director_container:
                            movie_info['director'] = {
                                'name': director_container.text,
                                'url': director_container.get('data-url')
                            }
                    genres = re.search(r'\((.*?)\)', span.text)
                    if genres:
                        movie_info['genre'] = [genre.strip() for genre in genres.group(1).split(',')]
                    for actor in span.find_all('a', {'class': 'lined'}):
                        if not actor.find_parent('i', {'class': 'director'}):
                            if actor.text != '...' and len(actor.text.strip()) > 0:
                                movie_info['actors'].append({
                                    'name': actor.text,
                                    'url': actor.get('data-url')
                                })
        print(movie_info)
        movies.append(movie_info)
    return movies


response = requests.get(search_url, headers=headers, stream=True, timeout=10)
print('response:', response.status_code, '\n')

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    most_wanted = soup.find('div', {'class': 'search_results'})
    search_movie_info(most_wanted)

    search_results = soup.find('div', {'class': 'search_results search_results_last'})
    search_movie_info(search_results)