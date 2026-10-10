"""Ручной поиск по каталогу Кинопоиска (MongoDB) для UI разбора.

Поиск идёт по обеим коллекциям (film/series), ввод экранируется через
re.escape (защита от ReDoS/полного скана), `type` возвращается как подсказка.
"""

import re

from planner.mongo_settings import mongo_connection
from film_index import normalization

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


def search_catalog(query: str, limit: int = 15) -> list:
    text = (query or '').strip()
    if not text:
        return []
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
    return results[:limit]
