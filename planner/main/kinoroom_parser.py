import datetime

from django.conf import settings
from django.db import connections
import os
import requests
from bs4 import BeautifulSoup

parent_directory = os.path.dirname(os.path.abspath(__file__))
banners_directory = os.path.join(os.path.dirname(parent_directory), 'static', 'banners')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}


def locate_url(program_id, program_name, year):
    if check_db(program_id):
        return f'/static/banners/{program_id}.jpg'
    else:
        try:
            url = search_movie_poster(program_id, program_name, year)
            return url
        except Exception as e:
            print(e)
            return f'/static/banners/no_poster.jpg'

def search_movie_poster(program_id, program_name, year):
    try:
        poster_path = os.path.join(settings.STATIC_BANNERS, f'{program_id}.jpg')
        if os.path.exists(poster_path):
            return 'success'
        program_name = program_name.replace('ё', 'е')
        program_name = program_name.replace('`', '')
        program_name = program_name.replace('’', '')
        program_name = program_name.replace('сезон', '')
        program_name = program_name.replace(' ', '%20')
        if '-' in year:
            year = year.strip().split('-')[0]
        elif '–' in year:
            year = year.strip().split('–')[0]
        search_url = f'https://ru.kinorium.com/search/?q={program_name}%20{year}'
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            movie_list = soup.find_all('a', {'class': 'search-page__title-link'})
            # scripts = soup.find_all("script", string=True)
            # for script in scripts:
            #     print('script', script.string)
            movie_id = [movie.get('href') for movie in movie_list if movie.text.rstrip().startswith(program_name[:7])]
            # movie_id = [movie.get('href') for movie in movie_list if movie.text.rstrip()]

            if movie_id:
                movie_id = movie_id[0].replace('/', '')
                poster_url = 'https://ru-images.kinorium.com/movie/400/' + movie_id + '.jpg'
                response = requests.get(poster_url, headers=headers)
                if response.status_code == 200:

                    return download_poster(program_id, poster_url)
                else:
                    movie_url = f'https://ru.kinorium.com/{movie_id}/'
                    response = requests.get(movie_url, headers=headers)
                    if response.status_code == 200:
                        search_url = BeautifulSoup(response.text, 'html.parser')
                        poster_url = search_url.find('img', {'class': 'movie_gallery_poster'}).get('src')
                        poster_url = poster_url.replace('/300/', '/400/')
                        response = requests.get(poster_url, headers=headers)
                        if response.status_code == 200:

                            return download_poster(program_id, poster_url)
            else:
                movie_id = soup.find('div', {'class': 'main_poster'})
                if movie_id:
                    movie_id = movie_id.get('data-movieid')
                    if movie_id:
                        poster_url = 'https://ru-images.kinorium.com/movie/400/' + movie_id + '.jpg'
                        response = requests.get(poster_url, headers=headers)
                        if response.status_code == 200:

                            return download_poster(program_id, poster_url)
    except Exception as e:
        print(e)
        return 'error'

def download_poster(program_id, movie_url):
    try:
        response = requests.get(movie_url, headers=headers)
        if response.status_code == 200:
            os.makedirs(banners_directory, exist_ok=True)
            image_filename = os.path.join(banners_directory, f'{program_id}.jpg')
            with open(image_filename, 'wb') as img_file:
                img_file.write(response.content)
            insert_into_db(program_id)
            return 'success'
    except Exception as e:
        print(e)
        return 'error'


def check_db(program_id):
    with connections['planner'].cursor() as cursor:
        query = f'''SELECT [in_work] FROM [planner].[dbo].[banner_list]
         WHERE [program_id] = {program_id}'''
        cursor.execute(query)
        in_work = cursor.fetchone()
        if in_work:
            return in_work[0]

def insert_into_db(program_id):
    date_of_addition = datetime.datetime.today().date()
    in_work = 1
    try:
        with connections['planner'].cursor() as cursor:
            query = f'''INSERT INTO [planner].[dbo].[banner_list]
             ([program_id], [date_of_addition], [in_work]) VALUES 
             ({program_id}, '{date_of_addition}', {in_work})'''
            cursor.execute(query)
    except Exception:
        print('not added')