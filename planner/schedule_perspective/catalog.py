"""Каталог материалов Кинопоиска + линковка с Oplan3.

Источник выбирается через `CATALOG_BACKEND`: PostgreSQL (`kinopoisk.titles`)
или MongoDB (`kinopoisk.film` / `kinopoisk.series`). По `kinopoisk_id` затем
смотрим в `film_material_index`, есть ли материал в нашей базе и какой у него
`oplan_program_id`.
"""

import re

from django.conf import settings
from django.db import connection

from film_index import pg_catalog
from planner.mongo_settings import mongo_connection

from schedule_perspective import constants

_PAGE_LIMIT = 20

_PROJECTION = {
    'kinopoisk_id': 1,
    'title': 1,
    'original_title': 1,
    'year': 1,
    'countries': 1,
    'genres': 1,
    'director': 1,
    'type': 1,
    'duration': 1,
    'rating': 1,
}


def _parse_kp(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _clean_year(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r'\d{4}', str(value))
    return int(match.group(0)) if match else None


def search(query, limit=_PAGE_LIMIT):
    """Единый список фильмов и сериалов с признаком «в базе»."""
    text = (query or '').strip()
    if not text:
        return []

    if settings.CATALOG_BACKEND == 'postgres':
        cards = {}
        for item in pg_catalog.search_catalog(text, limit=limit):
            kp_id = item['kp_id']
            cards[kp_id] = {
                'kinopoisk_id': kp_id,
                'title': item['title'],
                'original_title': item['original_title'],
                'year': item['year'],
                'countries': item['countries'],
                'genres': [],
                'director': item['director'],
                'duration': item['duration'],
                'rating': item['rating'],
                'kind': item['type'],
                'in_base': False,
                'oplan_program_id': None,
            }
        _apply_base_status(cards)
        return list(cards.values())

    regex = {'$regex': re.escape(text), '$options': 'i'}
    condition = {'$or': [{'title': regex}, {'original_title': regex}]}

    cards = {}
    for collection_name, kind in (('film', 'film'), ('series', 'series')):
        with mongo_connection(collection_name, db_name='kinopoisk') as collection:
            cursor = collection.find(condition, _PROJECTION).limit(limit)
            for doc in cursor:
                kp_id = _parse_kp(doc.get('kinopoisk_id'))
                if kp_id is None or kp_id in cards:
                    continue
                cards[kp_id] = {
                    'kinopoisk_id': kp_id,
                    'title': doc.get('title') or '',
                    'original_title': doc.get('original_title') or '',
                    'year': _clean_year(doc.get('year')),
                    'countries': doc.get('countries') or [],
                    'genres': doc.get('genres') or [],
                    'director': doc.get('director') or '',
                    'duration': doc.get('duration'),
                    'rating': doc.get('rating'),
                    'kind': kind,
                    'in_base': False,
                    'oplan_program_id': None,
                }

    _apply_base_status(cards)
    result = list(cards.values())
    result.sort(key=lambda c: (c.get('rating') or 0), reverse=True)
    return result[:limit]


def _apply_base_status(cards):
    if not cards:
        return
    kp_ids = list(cards.keys())
    placeholders = ', '.join(['%s'] * len(kp_ids))
    sql = f"""
    SELECT FMI.kinopoisk_id, FMI.oplan_program_id, FMI.has_file, Op.program_kind
    FROM dbo.film_material_index AS FMI
    LEFT JOIN [oplan3].dbo.program AS Op ON Op.program_id = FMI.oplan_program_id
    WHERE FMI.kinopoisk_id IN ({placeholders})
    """
    rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, kp_ids)
            rows = cursor.fetchall()
    except Exception as error:
        print('schedule_perspective catalog link error:', error)
        return
    for kp_id, oplan_program_id, has_file, program_kind in rows:
        card = cards.get(kp_id)
        if not card:
            continue
        if has_file:
            card['in_base'] = True
        if program_kind == constants.FILM_KIND and card['kind'] == 'film':
            card['oplan_program_id'] = oplan_program_id


def get_series_structure(kinopoisk_id):
    """Сезоны и серии сериала из Oplan3 (если он сопоставлен).

    Возвращает {'in_base': bool, 'seasons': [...]}. Для сериала, которого нет
    в Oplan, seasons пустой — редактор задаёт сезон/серию вручную.
    """
    sql = """
    SELECT Op.program_id, Op.parent_id, Op.program_kind, Op.episode_num,
           Op.name, Op.duration
    FROM dbo.film_material_index AS FMI
    JOIN [oplan3].dbo.program AS Op ON Op.program_id = FMI.oplan_program_id
    WHERE FMI.kinopoisk_id = %s
      AND Op.program_kind IN (3, 4)
      AND Op.deleted = 0 AND Op.DeletedIncludeParent = 0
    ORDER BY Op.parent_id, Op.episode_num
    """
    rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, (kinopoisk_id,))
            rows = cursor.fetchall()
    except Exception as error:
        print('schedule_perspective series structure error:', error)

    seasons = {}
    episodes_by_parent = {}
    for program_id, parent_id, program_kind, episode_num, name, duration in rows:
        if program_kind == constants.SEASON_KIND:
            seasons[program_id] = {
                'season_id': program_id,
                'label': name or f'Сезон {len(seasons) + 1}',
                'episodes': [],
            }
        elif program_kind == constants.EPISODE_KIND:
            episodes_by_parent.setdefault(parent_id, []).append({
                'oplan_program_id': program_id,
                'episode_num': episode_num,
                'duration': duration,
            })
    for parent_id, episodes in episodes_by_parent.items():
        season = seasons.get(parent_id)
        if season is None:
            season = seasons[parent_id] = {
                'season_id': parent_id,
                'label': f'Сезон {len(seasons) + 1}',
                'episodes': [],
            }
        season['episodes'] = episodes

    season_list = list(seasons.values())
    return {
        'kinopoisk_id': kinopoisk_id,
        'in_base': bool(season_list),
        'seasons': season_list,
    }


def get_duration_frames(kinopoisk_id):
    """Хронометраж из выбранного каталога (минуты) -> кадры."""
    if settings.CATALOG_BACKEND == 'postgres':
        try:
            duration = pg_catalog.get_duration_minutes(kinopoisk_id)
            if duration:
                return int(float(duration) * 60 * constants.FPS)
        except Exception as error:
            print('schedule_perspective duration error:', error)
        return constants.DEFAULT_DURATION_FRAMES

    condition = {'kinopoisk_id': {'$in': [str(kinopoisk_id), int(kinopoisk_id)]}}
    try:
        with mongo_connection('film', db_name='kinopoisk') as collection:
            doc = collection.find_one(condition, _PROJECTION)
        if doc is None:
            with mongo_connection('series', db_name='kinopoisk') as collection:
                doc = collection.find_one(condition, _PROJECTION)
        duration = (doc or {}).get('duration')
        if duration:
            return int(float(duration) * 60 * constants.FPS)
    except Exception as error:
        print('schedule_perspective duration error:', error)
    return constants.DEFAULT_DURATION_FRAMES
