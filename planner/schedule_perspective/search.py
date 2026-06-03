from django.db import connections
from pymongo import MongoClient

from planner.settings import OPLAN_DB, PLANNER_DB, MONGO_HOST


def fast_search(program_name) -> list:
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                       ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                       ('Progs', 'duration'), ('Adult', 'Name'), ('Task', 'worker_id'), ('Task', 'sched_id'),
                       ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status')]
            sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
            django_columns = [f'{col}_{val}' for col, val in columns]
            query = f'''
            SELECT TOP (4) {sql_columns}
            FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Task.[program_id] = Progs.[program_id]
            LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
                ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
            WHERE Progs.[deleted] = 0
            AND Progs.[name] LIKE '%{program_name}%'
            ORDER BY Progs.[name];
            '''
            cursor.execute(query)
            result = cursor.fetchall()
        search_list = [dict(zip(django_columns, task)) for task in result]
        return search_list
    except Exception as error:
        print(error)
        return []


def search_kinopoisk(program_name) -> list:
    """Поиск фильмов и сериалов в MongoDB по названию (title или original_title)"""
    try:
        from contextlib import contextmanager

        @contextmanager
        def mongo_connection(collection_name):
            client = None
            try:
                client = MongoClient(MONGO_HOST)
                db = client['kinopoisk']  # имя БД
                yield db[collection_name]
            finally:
                if client:
                    client.close()

        results = []
        regex_pattern = f'.*{program_name}.*'

        # Ищем в коллекции film
        with mongo_connection('film') as collection:
            cursor = collection.find({
                '$or': [
                    {'title': {'$regex': regex_pattern, '$options': 'i'}},
                    {'original_title': {'$regex': regex_pattern, '$options': 'i'}}
                ]
            }).limit(4).sort([('rating', -1)])
            for doc in cursor:
                results.append({
                    'kinopoisk_id': doc.get('kinopoisk_id', ''),
                    'title': doc.get('title', ''),
                    'original_title': doc.get('original_title', ''),
                    'year': doc.get('year', 0),
                    'duration': doc.get('duration', 0),
                    'rating': doc.get('rating', 0),
                    'genres': doc.get('genres', []),
                    'countries': doc.get('countries', []),
                    'director': doc.get('director', ''),
                    'actors': doc.get('actors', []),
                    'type': 'film',
                })

            # Ищем в коллекции series
        with mongo_connection('series') as collection:
            cursor = collection.find({
                '$or': [
                    {'title': {'$regex': regex_pattern, '$options': 'i'}},
                    {'original_title': {'$regex': regex_pattern, '$options': 'i'}}
                ]
            }).limit(4).sort([('rating', -1)])
            for doc in cursor:
                results.append({
                    'kinopoisk_id': doc.get('kinopoisk_id', ''),
                    'title': doc.get('title', ''),
                    'original_title': doc.get('original_title', ''),
                    'year': doc.get('year', 0),
                    'duration': doc.get('duration', 0),
                    'rating': doc.get('rating', 0),
                    'genres': doc.get('genres', []),
                    'countries': doc.get('countries', []),
                    'director': doc.get('director', ''),
                    'actors': doc.get('actors', []),
                    'type': 'series',
                })

        # Сортируем общий результат по рейтингу (если нужно)
        results.sort(key=lambda x: x['rating'], reverse=True)

        # Ограничиваем общее количество (опционально)
        return results[:8]

    except Exception as error:
        print('MongoDB search error:', error)
        return []