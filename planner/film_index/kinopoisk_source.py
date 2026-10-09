"""Источник данных Кинопоиска (MongoDB, db `kinopoisk`, коллекции film/series).

Каталог грузится в память один раз и индексируется:
* точный индекс по нормализованному названию/original_title;
* инвертированный индекс токенов - для быстрой генерации кандидатов под
  нечёткое сравнение (без полного перебора каталога).

Коллекциям не доверяем полностью (Кинопоиск иногда кладёт сериалы в films и
наоборот, бывает дублирование), поэтому film/series используются как мягкая
подсказка, а не как жёсткий фильтр.
"""

from collections import defaultdict

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

_MAX_DOC_FREQ = 5000      # слишком частые токены не считаем информативными
_MAX_CANDIDATES = 2000    # ограничение множества кандидатов на один запрос


class KinopoiskCatalog:
    def __init__(self, entries: list):
        self.entries = entries
        self._exact_title = defaultdict(list)
        self._exact_original = defaultdict(list)
        self._token_index = defaultdict(list)
        self._build_index()

    def _build_index(self) -> None:
        for index, entry in enumerate(self.entries):
            norm_title = entry['norm_title']
            norm_original = entry['norm_original']
            if norm_title:
                self._exact_title[norm_title].append(index)
            if norm_original:
                self._exact_original[norm_original].append(index)
            tokens = set(normalization.significant_tokens(norm_title))
            tokens.update(normalization.significant_tokens(norm_original))
            for token in tokens:
                self._token_index[token].append(index)

    @property
    def size(self) -> int:
        return len(self.entries)

    def _entry(self, index: int) -> dict:
        return self.entries[index]

    def candidate_indices(self, norm_title: str, norm_original: str) -> set:
        """Индексы потенциальных кандидатов по общим токенам названия."""
        exact = set(self._exact_title.get(norm_title, ()))
        exact.update(self._exact_original.get(norm_original, ()))
        if exact:
            return exact

        tokens = set(normalization.significant_tokens(norm_title))
        tokens.update(normalization.significant_tokens(norm_original))
        candidates = set()
        for token in tokens:
            bucket = self._token_index.get(token)
            if not bucket or len(bucket) > _MAX_DOC_FREQ:
                continue
            candidates.update(bucket)
            if len(candidates) > _MAX_CANDIDATES:
                break
        return candidates

    def entries_for(self, indices) -> list:
        return [self.entries[i] for i in indices]


def _build_entry(doc: dict) -> dict:
    kp_id = normalization.parse_kinopoisk_id(doc.get('kinopoisk_id'))
    title = doc.get('title') or ''
    original = doc.get('original_title') or ''
    director_names = normalization.director_names(doc.get('director'))
    director_tokens = normalization.person_tokens(director_names)
    return {
        'kp_id': kp_id,
        'title': title,
        'original_title': original,
        'year': normalization.clean_year(doc.get('year')),
        'countries': normalization.normalize_countries(doc.get('countries')),
        'director_names': director_names,
        'director_tokens': director_tokens,
        'type': doc.get('type'),
        'duration': doc.get('duration'),
        'rating': doc.get('rating'),
        'norm_title': normalization.normalize_title(title),
        'norm_original': normalization.normalize_title(original),
    }


def load_catalog() -> KinopoiskCatalog:
    """Загружает каталог film+series из Mongo в память."""
    entries = []
    seen = set()
    for collection_name in ('film', 'series'):
        with mongo_connection(collection_name, db_name='kinopoisk') as collection:
            cursor = collection.find({}, _PROJECTION)
            for doc in cursor:
                entry = _build_entry(doc)
                if entry['kp_id'] is None:
                    continue
                dedup_key = (entry['kp_id'], entry['type'])
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                entries.append(entry)
    return KinopoiskCatalog(entries)
