"""Батч метаданных для тултипов и хронометража.

Источник — PostgreSQL или Mongo по `CATALOG_BACKEND`. Кэш —
`django.core.cache` (Redis). Ошибка каталога не должна ломать рендер.
"""

from django.conf import settings
from django.core.cache import cache
from django.db import connection

from film_index import pg_catalog
from planner.settings import OPLAN_DB, PLANNER_DB
from planner.mongo_settings import mongo_connection

from schedule_perspective import constants

_PROJECTION = {
    'kinopoisk_id': 1,
    'title': 1,
    'original_title': 1,
    'year': 1,
    'countries': 1,
    'genres': 1,
    'director': 1,
    'actors': 1,
    'rating': 1,
    'rating_imdb': 1,
    'age_rating': 1,
    'duration': 1,
    'description': 1,
}


def _cache_key(kp_id):
    return f'sp_film_info_{settings.CATALOG_BACKEND}_{kp_id}'


def get_film_metadata(kp_ids):
    """kp_id -> метаданные (с кэшем)."""
    result = {}
    missing = []
    for kp_id in kp_ids:
        cached = cache.get(_cache_key(kp_id))
        if cached is not None:
            result[kp_id] = cached
        else:
            missing.append(kp_id)
    if missing:
        if settings.CATALOG_BACKEND == 'postgres':
            try:
                fetched = pg_catalog.get_titles_by_ids(missing)
            except Exception as error:
                print('schedule_perspective metadata error:', error)
                fetched = {}
        else:
            fetched = _load_mongo(missing)
        for kp_id, meta in fetched.items():
            cache.set(_cache_key(kp_id), meta, constants.METADATA_CACHE_SECONDS)
            result[kp_id] = meta
    return result


def _load_mongo(kp_ids):
    wanted = set()
    for kp_id in kp_ids:
        wanted.add(str(kp_id))
        wanted.add(int(kp_id))
    found = {}
    condition = {'kinopoisk_id': {'$in': list(wanted)}}
    for collection_name in ('film', 'series'):
        try:
            with mongo_connection(collection_name, db_name='kinopoisk') as collection:
                for doc in collection.find(condition, _PROJECTION):
                    kp_id = int(str(doc.get('kinopoisk_id')).strip())
                    if kp_id in found:
                        continue
                    found[kp_id] = {
                        'kinopoisk_id': kp_id,
                        'title': doc.get('title') or '',
                        'original_title': doc.get('original_title') or '',
                        'year': doc.get('year'),
                        'countries': doc.get('countries') or [],
                        'genres': doc.get('genres') or [],
                        'director': doc.get('director') or '',
                        'actors': (doc.get('actors') or [])[:10],
                        'rating': doc.get('rating'),
                        'rating_imdb': doc.get('rating_imdb'),
                        'age_rating': doc.get('age_rating'),
                        'duration': doc.get('duration'),
                        'description': doc.get('description'),
                    }
        except Exception as error:
            print('schedule_perspective metadata error:', error)
    return found


def get_oplan_metadata(program_ids):
    """program_id -> краткие данные Oplan3 (для тултипа/описания)."""
    program_ids = [pid for pid in program_ids if pid]
    if not program_ids:
        return {}
    placeholders = ', '.join(['%s'] * len(program_ids))
    sql = f"""
    SELECT P.program_id, P.name, P.orig_name, P.production_year,
           P.production_country, P.Director, P.episode_num, P.program_kind,
           FMI.has_file, FMI.kinopoisk_id
    FROM [{OPLAN_DB}].dbo.program AS P
    LEFT JOIN [{PLANNER_DB}].dbo.film_material_index AS FMI
        ON FMI.oplan_program_id = P.program_id
    WHERE P.program_id IN ({placeholders})
    """
    result = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, program_ids)
            columns = ('oplan_program_id', 'title', 'original_title', 'year',
                       'countries', 'director', 'episode_num', 'program_kind',
                       'has_file', 'kinopoisk_id')
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                item['in_base'] = bool(item.pop('has_file'))
                result[item['oplan_program_id']] = item
    except Exception as error:
        print('schedule_perspective oplan metadata error:', error)
    return result
