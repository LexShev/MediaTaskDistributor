"""Серверный кэш постеров Кинопоиска в отдельном бакете.

Постеры Oplan (kinorium) лежат в основном бакете под `posters/{program_id}.jpg`.
Здесь отдельный бакет `KP_POSTERS_BUCKET` и ключи `posters/{kp_id}.jpg`, чтобы
не смешивать источники. Поток: Django отдаёт байты из бакета, а при промахе
скачивает с Кинопоиска и кэширует.
"""

import logging

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger('planner.film_index.posters')

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
    )
}

_POSTER_SOURCES = (
    'https://st.kp.yandex.net/images/film_big/{id}.jpg',
    'https://st.kp.yandex.net/images/film_orig/{id}.jpg',
    'https://www.kinopoisk.ru/images/sm_film/{id}.jpg',
)


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
    except Exception as error:  # noqa: BLE001 - бакет может отсутствовать/нет прав
        logger.warning('Не удалось подготовить бакет постеров КП: %s', error)


def _fetch_from_kinopoisk(kp_id):
    for template in _POSTER_SOURCES:
        url = template.format(id=kp_id)
        try:
            response = requests.get(url, headers=_HEADERS, timeout=10)
        except requests.RequestException as error:
            logger.info('Постер КП %s недоступен (%s): %s', kp_id, url, error)
            continue
        if response.status_code != 200:
            continue
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'image' not in content_type:
            continue
        content = response.content
        if 1024 < len(content) < 10 * 1024 * 1024:
            return content, content_type
    return None, None


def get_poster(kp_id):
    """Возвращает (bytes, content_type) или (None, None)."""
    if not kp_id:
        return None, None
    storage = _get_storage()
    _ensure_bucket(storage)
    name = f'posters/{kp_id}.jpg'

    try:
        if storage.exists(name):
            with storage.open(name, 'rb') as file:
                return file.read(), 'image/jpeg'
    except Exception as error:  # noqa: BLE001
        logger.info('Чтение постера КП из бакета не удалось: %s', error)

    content, content_type = _fetch_from_kinopoisk(kp_id)
    if content is None:
        return None, None

    try:
        storage.save(name, ContentFile(content))
    except Exception as error:  # noqa: BLE001 - кэш необязателен
        logger.info('Кэширование постера КП %s не удалось: %s', kp_id, error)
    return content, content_type
