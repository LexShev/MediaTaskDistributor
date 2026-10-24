"""Import the SQLite Kinopoisk catalog into PostgreSQL."""

import hashlib
import json
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from film_index import normalization


STAGE_TABLE = 'pg_temp.kinopoisk_import_stage'

STAGE_SQL = """
CREATE TEMP TABLE kinopoisk_import_stage (
    kp_id                integer,
    imdb_id              text,
    tmdb_id              integer,
    type                 text,
    ru_name              text,
    eng_name             text,
    original_name        text,
    year                 smallint,
    start_year           smallint,
    end_year             smallint,
    status               text,
    duration_min         integer,
    country              text[],
    genre                text[],
    keywords             text[],
    production_companies text[],
    director_names       text[],
    kp_rating            numeric(3,1),
    imdb_rating          numeric(3,1),
    tmdb_rating          numeric(3,1),
    poster_url           text,
    poster_url_preview   text,
    short_description    text,
    description          text,
    slogan               text,
    budget               text,
    content_hash         text,
    payload              jsonb,
    search_text          text
) ON COMMIT DROP
"""

PARSED_PAYLOAD_FIELDS = (
    'director',
    'screenwriter',
    'producer',
    'operator',
    'composer',
    'artist',
    'editor',
    'main_actors',
    'voice',
    'originals',
    'content_rating',
    'seasons',
    'sequels',
    'parents_guide',
    'facts',
    'awards',
    'box_office',
    'simular',
    'release_dates',
    'premiere',
)


def _parse_json(value):
    if value is None or value == '':
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def _as_int(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_year(value):
    number = _as_int(value)
    return number if number and number > 0 else None


def _as_float(value):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_list(value):
    parsed = _parse_json(value)
    if parsed is None:
        return []
    if not isinstance(parsed, list):
        parsed = [parsed]
    result = []
    seen = set()
    for item in parsed:
        if isinstance(item, dict):
            item = item.get('nameRu') or item.get('name') or item.get('nameEn')
        text = _as_text(item)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _as_director_names(value):
    names = []
    parsed = _parse_json(value)
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                item = item.get('nameRu') or item.get('name') or item.get('nameEn')
            text = _as_text(item)
            if text:
                names.append(text)
    elif parsed:
        names.append(str(parsed))
    return normalization.director_names(names)


def _content_hash(row) -> str:
    raw = json.dumps(list(row), ensure_ascii=False, default=str, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _payload(row) -> dict:
    return {field: _parse_json(row[field]) for field in PARSED_PAYLOAD_FIELDS}


class Command(BaseCommand):
    help = 'Импортирует db/media.sqlite3 в PostgreSQL-каталог kinopoisk.*'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            required=True,
            help='Путь к SQLite-базе Кинопоиска (например, /app/db/media.sqlite3)',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Очистить kinopoisk.titles перед импортом',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Импортировать только первые N строк (для проверки)',
        )
        parser.add_argument(
            '--db-alias',
            default=settings.CATALOG_ADMIN_DB,
            help='Django-алиас PostgreSQL (по умолчанию catalog_admin)',
        )

    def handle(self, *args, **options):
        source = Path(options['source'])
        if not source.exists():
            raise CommandError(f'SQLite-база не найдена: {source}')

        limit = options.get('limit')
        replace = options.get('replace')
        db_alias = options['db_alias']

        self._ensure_schema(db_alias)
        with connections[db_alias].cursor() as cursor:
            cursor.execute(
                "INSERT INTO sync.runs (source, status) VALUES (%s, %s) RETURNING id",
                [str(source), 'running'],
            )
            run_id = cursor.fetchone()[0]

        rows_read = rows_written = 0
        try:
            with transaction.atomic(using=db_alias):
                with connections[db_alias].cursor() as cursor:
                    if replace:
                        cursor.execute('TRUNCATE kinopoisk.titles CASCADE')
                    else:
                        cursor.execute('SELECT count(*) FROM kinopoisk.titles')
                        if cursor.fetchone()[0]:
                            raise CommandError(
                                'kinopoisk.titles не пуста. Используйте --replace '
                                'или очистите таблицы вручную.'
                            )
                    cursor.execute(STAGE_SQL)

                connection = connections[db_alias].connection
                with connection.cursor() as stage_cursor:
                    with stage_cursor.copy(
                        f"""
                        COPY {STAGE_TABLE} (
                            kp_id, imdb_id, tmdb_id, type, ru_name, eng_name,
                            original_name, year, start_year, end_year, status,
                            duration_min, country, genre, keywords,
                            production_companies, director_names, kp_rating,
                            imdb_rating, tmdb_rating, poster_url,
                            poster_url_preview, short_description, description,
                            slogan, budget, content_hash, payload, search_text
                        ) FROM STDIN
                        """
                    ) as stage_copy:
                        for row in self._rows(source, limit):
                            rows_read += 1
                            item = self._row_values(row)
                            stage_copy.write_row(item['titles'] + (
                                json.dumps(item['payload'], ensure_ascii=False, default=str),
                                item['search_text'],
                            ))
                            rows_written += 1
                            if rows_written % 100000 == 0:
                                self.stdout.write(f'  ... {rows_written} строк')

                with connections[db_alias].cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO kinopoisk.titles (
                            kp_id, imdb_id, tmdb_id, type, ru_name, eng_name,
                            original_name, year, start_year, end_year, status,
                            duration_min, country, genre, keywords,
                            production_companies, director_names, kp_rating,
                            imdb_rating, tmdb_rating, poster_url,
                            poster_url_preview, short_description, description,
                            slogan, budget, content_hash
                        )
                        SELECT
                            kp_id, imdb_id, tmdb_id, type, ru_name, eng_name,
                            original_name, year, start_year, end_year, status,
                            duration_min, country, genre, keywords,
                            production_companies, director_names, kp_rating,
                            imdb_rating, tmdb_rating, poster_url,
                            poster_url_preview, short_description, description,
                            slogan, budget, content_hash
                        FROM {STAGE_TABLE}
                        """
                    )
                    cursor.execute(
                        f"""
                        INSERT INTO kinopoisk.title_payload (kp_id, payload)
                        SELECT kp_id, payload FROM {STAGE_TABLE}
                        """
                    )
                    cursor.execute(
                        f"""
                        INSERT INTO kinopoisk.title_search (
                            kp_id, search_text, type, year, kp_rating
                        )
                        SELECT kp_id, search_text, type, year, kp_rating
                        FROM {STAGE_TABLE}
                        """
                    )
                    cursor.execute('ANALYZE kinopoisk.titles')
                    cursor.execute('ANALYZE kinopoisk.title_payload')
                    cursor.execute('ANALYZE kinopoisk.title_search')
                    cursor.execute(
                        """
                        UPDATE sync.runs
                        SET finished_at = now(), status = 'ok',
                            rows_read = %s, rows_written = %s
                        WHERE id = %s
                        """,
                        [rows_read, rows_written, run_id],
                    )
        except Exception as error:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE sync.runs
                    SET finished_at = now(), status = 'error',
                        rows_read = %s, rows_written = %s, error = %s
                    WHERE id = %s
                    """,
                    [rows_read, rows_written, str(error), run_id],
                )
            raise

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано строк: {rows_written} (прочитано {rows_read})'
        ))

    def _rows(self, source: Path, limit):
        uri = f'file:{source.as_posix()}?mode=ro'
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        try:
            query = 'SELECT * FROM media_items'
            if limit:
                query += f' LIMIT {int(limit)}'
            yield from connection.execute(query)
        finally:
            connection.close()

    def _row_values(self, row):
        kp_id = _as_int(row['kp_id'])
        if kp_id is None:
            raise CommandError('Найдена строка без числового kp_id')

        type_ = _as_text(row['type'])
        if type_ not in ('film', 'series'):
            raise CommandError(f'Неизвестный type={type_!r} у kp_id={kp_id}')

        ru_name = _as_text(row['ru_name'])
        eng_name = _as_text(row['eng_name'])
        original_name = _as_text(row['original_name'])
        start_year = _as_year(row['start_year'])
        year = start_year or _as_year(row['date_published'])
        end_year = _as_year(row['end_year'])
        kp_rating = _as_float(row['kp_rating'])
        search_parts = []
        for name in (ru_name, eng_name, original_name):
            normalized_name = normalization.normalize_search_text(name)
            if normalized_name and normalized_name not in search_parts:
                search_parts.append(normalized_name)
        search_text = ' '.join(search_parts)

        titles = (
            kp_id,
            _as_text(row['imdb_id']),
            _as_int(row['tmdb_id']),
            type_,
            ru_name,
            eng_name,
            original_name,
            year,
            start_year,
            end_year,
            _as_text(row['status']),
            _as_int(row['duration']),
            _as_list(row['country']),
            _as_list(row['genre']),
            _as_list(row['keywords']),
            _as_list(row['production_companies']),
            _as_director_names(row['director']),
            kp_rating,
            _as_float(row['imdb_rating']),
            _as_float(row['tmdb_rating']),
            _as_text(row['poster_url']),
            _as_text(row['poster_url_preview']),
            _as_text(row['short_description']),
            _as_text(row['description']),
            _as_text(row['slogan']),
            _as_text(row['budget']),
            _content_hash(row),
        )

        return {
            'kp_id': kp_id,
            'titles': titles,
            'payload': _payload(row),
            'search_text': search_text,
            'search': (kp_id, search_text, type_, year, kp_rating),
        }

    def _ensure_schema(self, db_alias):
        sql_path = Path(settings.BASE_DIR).parent / 'sql_scripts' / 'postgres' / '001_kinopoisk.sql'
        if not sql_path.exists():
            raise CommandError(f'Не найден SQL-файл схемы: {sql_path}')
        sql = sql_path.read_text(encoding='utf-8')
        statements = [statement.strip() for statement in sql.split(';') if statement.strip()]
        with connections[db_alias].cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
