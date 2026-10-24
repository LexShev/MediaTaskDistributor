"""PostgreSQL-backed Kinopoisk catalog and title search."""

from django.conf import settings
from django.db import connections, transaction

from film_index import normalization


def _row_value(row, key, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _build_entry(row) -> dict:
    kp_id = _row_value(row, 'kp_id')
    title = _row_value(row, 'ru_name') or _row_value(row, 'eng_name') or _row_value(row, 'original_name') or ''
    original = _row_value(row, 'eng_name') or _row_value(row, 'original_name') or ''
    director_names = list(_row_value(row, 'director_names') or [])
    rating = _row_value(row, 'kp_rating')
    return {
        'kp_id': kp_id,
        'title': title,
        'original_title': original,
        'year': _row_value(row, 'year'),
        'countries': normalization.normalize_countries(_row_value(row, 'country') or []),
        'director_names': director_names,
        'director_tokens': normalization.person_tokens(director_names),
        'type': _row_value(row, 'type'),
        'duration': _row_value(row, 'duration_min'),
        'rating': float(rating) if rating is not None else None,
        'norm_title': normalization.normalize_title(title),
        'norm_original': normalization.normalize_title(original),
    }


def load_catalog() -> list:
    """Load the full Kinopoisk catalog from PostgreSQL."""
    entries = []
    seen = set()
    with connections[settings.CATALOG_DB].chunked_cursor() as cursor:
        cursor.execute(
            """
            SELECT kp_id, ru_name, eng_name, original_name, year,
                   country, director_names, type, duration_min, kp_rating
            FROM kinopoisk.titles
            ORDER BY kp_id
            """
        )
        columns = [column[0] for column in cursor.description]
        while True:
            rows = cursor.fetchmany(2000)
            if not rows:
                break
            for row in rows:
                entry = _build_entry(dict(zip(columns, row)))
                if entry['kp_id'] is None:
                    continue
                dedup_key = (entry['kp_id'], entry['type'])
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                entries.append(entry)
    return entries


def _title_values(ru_name, eng_name, original_name):
    title = ru_name or eng_name or original_name or ''
    original = eng_name or original_name or ''
    return title, original


def _as_float(value):
    return float(value) if value is not None else None


def get_titles_by_ids(kp_ids) -> dict:
    """Return schedule-perspective metadata for the given Kinopoisk ids."""
    ids = set()
    for value in kp_ids:
        try:
            ids.add(int(value))
        except (TypeError, ValueError):
            continue
    if not ids:
        return {}

    with connections[settings.CATALOG_DB].cursor() as cursor:
        cursor.execute(
            """
            SELECT kp_id, ru_name, eng_name, original_name, year,
                   country, genre, director_names, kp_rating, imdb_rating,
                   duration_min,
                   COALESCE(NULLIF(description, ''), short_description) AS description
            FROM kinopoisk.titles
            WHERE kp_id = ANY(%s)
            """,
            [sorted(ids)],
        )
        rows = cursor.fetchall()

    result = {}
    for row in rows:
        kp_id = row[0]
        title, original = _title_values(row[1], row[2], row[3])
        result[kp_id] = {
            'kinopoisk_id': kp_id,
            'title': title,
            'original_title': original,
            'year': row[4],
            'countries': list(row[5] or []),
            'genres': list(row[6] or []),
            'director': ', '.join(row[7] or []),
            'actors': [],
            'rating': _as_float(row[8]),
            'rating_imdb': _as_float(row[9]),
            'age_rating': None,
            'duration': row[10],
            'description': row[11],
        }
    return result


def get_duration_minutes(kp_id):
    try:
        kp_id = int(kp_id)
    except (TypeError, ValueError):
        return None
    with connections[settings.CATALOG_DB].cursor() as cursor:
        cursor.execute(
            'SELECT duration_min FROM kinopoisk.titles WHERE kp_id = %s',
            [kp_id],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def search_catalog(query: str, limit: int = 20) -> list:
    """Search titles through the pg_trgm index."""
    text = normalization.normalize_search_text(query)
    if not text:
        return []

    like_text = text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

    with transaction.atomic(using=settings.CATALOG_DB):
        with connections[settings.CATALOG_DB].cursor() as cursor:
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, true)",
                [str(settings.CATALOG_PG_TIMEOUT_MS)],
            )
            cursor.execute(
                """
                SELECT t.kp_id, t.ru_name, t.eng_name, t.original_name, t.year,
                       t.country, t.director_names, t.type, t.duration_min, t.kp_rating
                FROM kinopoisk.title_search s
                JOIN kinopoisk.titles t USING (kp_id)
                WHERE s.search_text LIKE %s OR s.search_text %% %s
                ORDER BY
                    similarity(s.search_text, %s) DESC,
                    t.kp_rating DESC NULLS LAST
                LIMIT %s
                """,
                [f'%{like_text}%', text, text, limit],
            )
            rows = cursor.fetchall()

    return [
        {
            'kp_id': row[0],
            'title': row[1] or row[2] or row[3] or '',
            'original_title': row[2] or row[3] or '',
            'year': row[4],
            'countries': list(row[5] or []),
            'director': ', '.join(row[6] or []),
            'type': row[7],
            'duration': row[8],
            'rating': float(row[9]) if row[9] is not None else None,
        }
        for row in rows
    ]
