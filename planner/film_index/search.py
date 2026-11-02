"""Ручной поиск по каталогу Кинопоиска для UI разбора.

При `CATALOG_BACKEND=postgres` поиск идёт через `pg_trgm`; иначе — по
коллекциям Mongo (film/series). В Mongo-ветке ввод экранируется через
re.escape (защита от ReDoS/полного скана), `type` возвращается как подсказка.
"""

import re

from django.conf import settings

from planner.mongo_settings import mongo_connection
from film_index import normalization, pg_catalog

_PROJECTION = {
    'kinopoisk_id': 1,
    'title': 1,
    'original_title': 1,
    'year': 1,
    'countries': 1,
    'director': 1,
    'type': 1,
    'duration': 1,
    'rating': 1,
}


def search_catalog(query: str, limit: int = 15) -> dict:
    """Ручной поиск: "Название" или "Название 1962" (год ±1).

    Возвращает ``{'items', 'title', 'year'}``. Mongo-ветка оставлена без
    изменений: там год не разбирается, база считается устаревшей.
    """
    text = (query or '').strip()
    if not text:
        return {'items': [], 'title': '', 'year': None}

    if settings.CATALOG_BACKEND == 'postgres':
        title, year = normalization.split_title_year(text)
        items = pg_catalog.search_catalog(title, limit=limit, year=year)
        if year is not None and not items:
            # Число могло быть частью названия ("Космическая одиссея 2001").
            fallback = pg_catalog.search_catalog(text, limit=limit)
            if fallback:
                return {'items': fallback, 'title': text, 'year': None}
        return {'items': items, 'title': title, 'year': year}

    regex = {'$regex': re.escape(text), '$options': 'i'}
    condition = {'$or': [{'title': regex}, {'original_title': regex}]}

    results = []
    seen = set()
    for collection_name in ('film', 'series'):
        with mongo_connection(collection_name, db_name='kinopoisk') as collection:
            cursor = collection.find(condition, _PROJECTION).limit(limit)
            for doc in cursor:
                kp_id = normalization.parse_kinopoisk_id(doc.get('kinopoisk_id'))
                if kp_id is None or kp_id in seen:
                    continue
                seen.add(kp_id)
                results.append({
                    'kp_id': kp_id,
                    'title': doc.get('title') or '',
                    'original_title': doc.get('original_title') or '',
                    'year': normalization.clean_year(doc.get('year')),
                    'countries': list(normalization.normalize_countries(doc.get('countries'))),
                    'director': doc.get('director') or '',
                    'type': doc.get('type'),
                    'duration': doc.get('duration'),
                    'rating': doc.get('rating'),
                })
    results.sort(key=lambda item: item.get('rating') or 0, reverse=True)
    return {'items': results[:limit], 'title': text, 'year': None}


def lookup_by_kp_id(kp_id):
    """Карточка каталога по kinopoisk_id. Для Mongo возвращает None."""
    try:
        kp_id = int(kp_id)
    except (TypeError, ValueError):
        return None
    if not (1 <= kp_id <= normalization.MAX_KP_ID):
        return None
    if settings.CATALOG_BACKEND != 'postgres':
        return None
    return pg_catalog.get_title_by_id(kp_id)


def resolve_kinopoisk_reference(query: str) -> dict:
    """Разбирает ссылку/ID Кинопоиска и ищет карточку в каталоге."""
    kp_id = normalization.extract_kinopoisk_id(query)
    if kp_id is None:
        return {
            'status': 'error',
            'message': (
                'Не удалось распознать ссылку. Нужна ссылка на фильм или '
                'сериал Кинопоиска либо числовой ID'
            ),
        }
    item = lookup_by_kp_id(kp_id)
    return {
        'status': 'success',
        'kp_id': kp_id,
        'found': item is not None,
        'item': item,
    }
