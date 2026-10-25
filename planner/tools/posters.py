"""Единый сервис постеров: Кинопоиск, S3-кэш и kinorium-fallback."""

import logging

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import connections
from storages.backends.s3boto3 import S3Boto3Storage

from planner.settings import OPLAN_DB

logger = logging.getLogger('planner.tools.posters')

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
    )
}

_DERIVED_SOURCES = (
    'https://st.kp.yandex.net/images/film_big/{id}.jpg',
    'https://st.kp.yandex.net/images/film_orig/{id}.jpg',
    'https://www.kinopoisk.ru/images/sm_film/{id}.jpg',
)

_MIN_SIZE = 1024
_MAX_SIZE = 10 * 1024 * 1024

_LEGACY_KEY = 'posters/{program_id}.jpg'
_KP_PROGRAM_KEY = 'programs/{program_id}.jpg'
_KP_CACHE_KEY = 'kp/{kp_id}.jpg'


class KinopoiskPosterStorage(S3Boto3Storage):
    bucket_name = getattr(settings, 'KP_POSTERS_BUCKET', 'kinopoisk-posters')
    location = ''
    default_acl = getattr(settings, 'AWS_DEFAULT_ACL', 'private')
    querystring_auth = True


_storage = None
_bucket_checked = False


def _get_storage():
    global _storage
    if _storage is None:
        _storage = KinopoiskPosterStorage()
    return _storage


def _ensure_bucket(storage):
    global _bucket_checked
    if _bucket_checked:
        return
    try:
        client = storage.connection.meta.client
        try:
            client.head_bucket(Bucket=storage.bucket_name)
        except Exception:
            client.create_bucket(Bucket=storage.bucket_name)
        _bucket_checked = True
    except Exception as error:
        logger.warning('Не удалось подготовить бакет постеров КП: %s', error)


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _guess_content_type(content):
    if content.startswith(b'\x89PNG'):
        return 'image/png'
    if content.startswith(b'RIFF') and content[8:12] == b'WEBP':
        return 'image/webp'
    return 'image/jpeg'


def _read(storage, name):
    try:
        if not storage.exists(name):
            return None, None
        with storage.open(name, 'rb') as file:
            content = file.read()
    except Exception as error:
        logger.info('Чтение постера %s не удалось: %s', name, error)
        return None, None
    return content, _guess_content_type(content)


def _save(storage, name, content):
    try:
        if storage.exists(name):
            storage.delete(name)
        storage.save(name, ContentFile(content))
    except Exception as error:
        logger.info('Кэширование постера %s не удалось: %s', name, error)


def _download(url):
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10)
    except requests.RequestException as error:
        logger.info('Постер недоступен (%s): %s', url, error)
        return None

    if response.status_code != 200:
        return None

    content_type = response.headers.get('content-type', '').lower()
    if 'image' not in content_type:
        return None

    content = response.content
    if not _MIN_SIZE < len(content) < _MAX_SIZE:
        return None
    return content


def _load_kp_sources(kp_id):
    db_url = None
    preview_url = None
    try:
        with connections[settings.CATALOG_DB].cursor() as cursor:
            cursor.execute(
                'SELECT poster_url, poster_url_preview FROM kinopoisk.titles WHERE kp_id = %s',
                [kp_id],
            )
            row = cursor.fetchone()
    except Exception as error:
        logger.info('Не удалось получить ссылки постера КП %s: %s', kp_id, error)
        row = None

    if row:
        db_url, preview_url = row

    sources = []
    if db_url:
        sources.append(db_url)
    sources.extend(template.format(id=kp_id) for template in _DERIVED_SOURCES)
    if preview_url:
        sources.append(preview_url)
    return sources


def _fetch_kp(kp_id):
    for url in _load_kp_sources(kp_id):
        content = _download(url)
        if content:
            return content
    return None


def _oplan_program_info(program_id):
    try:
        with connections[OPLAN_DB].cursor() as cursor:
            cursor.execute(
                f'SELECT name, production_year, production_country '
                f'FROM [{OPLAN_DB}].dbo.program WHERE program_id = %s',
                [program_id],
            )
            row = cursor.fetchone()
    except Exception as error:
        logger.info('Не удалось получить данные программы %s: %s', program_id, error)
        return None

    if not row:
        return None
    return {'title': row[0] or '', 'year': row[1] or '', 'country': row[2] or ''}


def _fetch_kinorium(program_id):
    info = _oplan_program_info(program_id)
    if info is None:
        return None

    from main.kinoroom_parser import download_poster, search

    query = {
        'program_id': program_id,
        'title': info['title'],
        'year': info['year'],
        'country': info['country'],
    }
    match = search(query)
    if not match:
        return None

    result = download_poster(program_id, match['movie']['data-id'])
    if result != 'success':
        return None

    content, _ = _read(default_storage, _LEGACY_KEY.format(program_id=program_id))
    return content


def get_poster(program_id=None, kp_id=None):
    """Возвращает (bytes, content_type) или (None, None)."""
    program_id = _as_int(program_id)
    kp_id = _as_int(kp_id)
    if not program_id and not kp_id:
        return None, None

    storage = _get_storage()
    _ensure_bucket(storage)

    if program_id:
        content, content_type = _read(storage, _KP_PROGRAM_KEY.format(program_id=program_id))
        if content is not None:
            return content, content_type
        content, content_type = _read(default_storage, _LEGACY_KEY.format(program_id=program_id))
        if content is not None:
            return content, content_type

    if kp_id:
        content, content_type = _read(storage, _KP_CACHE_KEY.format(kp_id=kp_id))
        if content is not None:
            return content, content_type

        content = _fetch_kp(kp_id)
        if content is not None:
            content_type = _guess_content_type(content)
            if program_id:
                _save(storage, _KP_PROGRAM_KEY.format(program_id=program_id), content)
            else:
                _save(storage, _KP_CACHE_KEY.format(kp_id=kp_id), content)
            return content, content_type

    if program_id:
        content = _fetch_kinorium(program_id)
        if content is not None:
            content_type = _guess_content_type(content)
            _save(default_storage, _LEGACY_KEY.format(program_id=program_id), content)
            return content, content_type

    return None, None


def delete_poster(program_id, dry_run=False):
    """Удаляет постеры программы из KP-бакета и legacy-бакета."""
    program_id = _as_int(program_id)
    if not program_id:
        return {}

    storage = _get_storage()
    targets = (
        (storage, _KP_PROGRAM_KEY.format(program_id=program_id)),
        (default_storage, _LEGACY_KEY.format(program_id=program_id)),
    )
    result = {}
    for target_storage, name in targets:
        try:
            if not target_storage.exists(name):
                result[name] = 'missing'
                continue
            if dry_run:
                result[name] = 'would-delete'
                continue
            target_storage.delete(name)
            result[name] = 'deleted'
        except Exception as error:
            result[name] = f'error: {error}'
    return result
