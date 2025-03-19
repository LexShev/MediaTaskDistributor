import os
import requests
from bs4 import BeautifulSoup


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

def search_movie(program_id, program_name, year):
    program_name = program_name.replace('ё', 'е')
    program_name = program_name.replace('серия', '')
    search_url = f'https://ru.kinorium.com/search/?q={program_name}%20{year}'

    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_list = soup.find_all('a', {'class': 'search-page__title-link'})
        movie_id = [movie.get('href') for movie in movie_list if movie.text.rstrip().startswith(program_name[:7])]
        # movie_id = [movie.get('href') for movie in movie_list if movie.text.rstrip()]
        if movie_id:
            movie_id = movie_id[0].replace('/', '')
            movie_url = 'https://ru-images.kinorium.com/movie/400/' + movie_id + '.jpg'
            return movie_url
        else:
            movie_id = soup.find('div', {'class': 'main_poster'})

            if movie_id:
                movie_id = movie_id.get('data-movieid')
                if movie_id:
                    movie_url = 'https://ru-images.kinorium.com/movie/400/' + movie_id + '.jpg'
                    return movie_url


def download_poster(program_id, program_name, year, movie_url):
    response = requests.get(movie_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        img = soup.find('img', {'class': 'card-header-poster'})
        poster_path = img.get('src')
        response = requests.get(poster_path)
        if response.status_code == 200:
            # image_filename = os.path.join('dog_images', f'{name}.jpg')
            with open(f'{program_id}_{program_name}_{year}.jpg', 'wb') as img_file:
                img_file.write(response.content)
        return poster_path

