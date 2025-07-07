import os
import requests
from bs4 import BeautifulSoup


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

def search_movie(program_id, program_name, year=1):
    program_name = program_name.replace('ё', 'е')
    search_url = f'https://www.imdb.com/find/?q={program_name}%20{year}&ref_=nv_sr_sm'
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_table = soup.find('ul', {'class': 'ipc-metadata-list'})
        movie_list = soup.find_all('a', {'class': 'ipc-metadata-list-summary-item__t'})
        find_res = [movie.get('href') for movie in movie_list if movie.text == program_name]
        if find_res:
            movie_url = 'https://www.imdb.com/'+find_res[0]
            return download_poster(program_id, program_name, year, movie_url)


def download_poster(program_id, program_name, year, movie_url):
    response = requests.get(movie_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        img = soup.find('img', {'class': 'ipc-image'})
        poster_path = [i for i in img.get('srcset').split(' ') if i.startswith('http')][-1]
        orig_poster_path = img.get('src').split('@')[0]+'@.jpg'
        # print(poster_path)
        # print(orig_poster_path)

        response = requests.get(poster_path)
        if response.status_code == 200:
            # image_filename = os.path.join('dog_images', f'{name}.jpg')
            with open(f'{program_id}_{program_name}_{year}.jpg', 'wb') as img_file:
                img_file.write(response.content)
        return poster_path
