"""Веб-интерфейс ручного разбора сопоставления film_index."""

import json
import logging
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from pymongo.errors import PyMongoError

from main.decorators import ajax_login_required
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from film_index import constants, normalization, repository, review, schema
from film_index.oplan_source import fetch_description, fetch_material
from film_index.search import search_catalog

logger = logging.getLogger(__name__)


def _is_chief_editor(user) -> bool:
    """Главный редактор: может забрать карточку у другого редактора."""
    return user.groups.filter(name='chief_editor').exists()


def _has_review_access(user) -> bool:
    """Доступ к странице и API ручного разбора."""
    return (
        user.is_authenticated
        and user.groups.filter(name__in=constants.ACCESS_GROUPS).exists()
    )


def review_api_access_required(view_func):
    """JSON-версия проверки доступа для API-эндпоинтов."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _has_review_access(request.user):
            return JsonResponse(
                {'status': 'error', 'message': 'Нет доступа'},
                status=403,
            )
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required()
def review_page(request):
    if not _has_review_access(request.user):
        raise PermissionDenied('Недостаточно прав для просмотра синхронизации с Кинопоиском')
    user_id = request.user.id
    user_group = request.user.groups.first().id
    try:
        schema.ensure_schema_once()
    except DatabaseError:
        logger.exception('Не удалось проверить схему film_index')
    data = {
        'stats': repository.review_stats(),
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group),
        'fps': constants.FPS,
        'channels': constants.CHANNELS,
        'is_chief_editor': _is_chief_editor(request.user),
        'lock_heartbeat_ms': constants.LOCK_HEARTBEAT_SECONDS * 1000,
    }
    return render(request, 'film_index/review.html', data)


@ajax_login_required
@review_api_access_required
def api_queue(request):
    kind = request.GET.get('kind') or None
    parent_id = request.GET.get('parent_id')
    try:
        parent_id = int(parent_id) if parent_id not in (None, '') else None
    except ValueError:
        parent_id = None
    status = request.GET.get('status') or 'pending'
    bucket = request.GET.get('bucket') or None
    channel = request.GET.get('channel') or None
    if channel and channel != 'none' and not channel.isdigit():
        channel = None
    name = request.GET.get('name') or None
    try:
        limit = int(request.GET.get('limit') or 500)
    except ValueError:
        limit = 500
    limit = max(1, min(limit, 500))
    try:
        offset = int(request.GET.get('offset') or 0)
    except ValueError:
        offset = 0
    offset = max(0, offset)
    items = repository.fetch_review_queue(
        status=status,
        bucket=bucket,
        kind=kind,
        parent_id=parent_id,
        name=name,
        channel=channel,
        limit=limit,
        offset=offset,
    )
    total = repository.count_review_queue(
        status=status,
        bucket=bucket,
        kind=kind,
        parent_id=parent_id,
        name=name,
        channel=channel,
    )
    return JsonResponse({
        'status': 'success', 'items': items, 'count': len(items),
        'total': total, 'offset': offset, 'limit': limit,
    })


@ajax_login_required
@review_api_access_required
def api_item(request, program_id):
    review_item = repository.fetch_review_item(program_id)
    material = fetch_material(program_id)
    if material is None:
        return JsonResponse({'status': 'error', 'message': 'Материал не найден'}, status=404)
    candidates = []
    if review_item and review_item.get('candidates_json'):
        try:
            candidates = json.loads(review_item['candidates_json'])
        except (TypeError, ValueError):
            candidates = []
    description = (fetch_description(program_id)
                   or material.get('short_annotation')
                   or material.get('annotation'))
    # Title Case только для UI: в matching режиссёры остаются нормализованными.
    material['director'] = normalization.format_person_names(material.get('director'))
    for candidate in candidates:
        if isinstance(candidate, dict):
            candidate['director'] = normalization.format_person_names(
                candidate.get('director')
            )
    return JsonResponse({
        'status': 'success',
        'material': material,
        'description': description,
        'review': {
            'status': review_item.get('status') if review_item else None,
            'bucket': review_item.get('bucket') if review_item else None,
            'resolved_kp_id': review_item.get('resolved_kp_id') if review_item else None,
        },
        'candidates': candidates,
    })


@ajax_login_required
@review_api_access_required
def api_search(request):
    query = request.GET.get('q') or ''
    try:
        items = search_catalog(query)
    except (DatabaseError, PyMongoError):
        logger.exception('Поиск по каталогу Кинопоиска не удался (q=%r)', query)
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Поиск временно недоступен, попробуйте ещё раз',
            },
            status=503,
        )
    return JsonResponse({'status': 'success', 'items': items})


@ajax_login_required
@review_api_access_required
@require_POST
def api_decide(request):
    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Некорректный JSON'}, status=400)

    action = payload.get('action')
    program_id = payload.get('program_id')
    user_id = request.user.id

    if action == 'accept':
        result = review.resolve(program_id, payload.get('kp_id'), user_id)
    elif action == 'reject':
        result = review.reject(program_id, user_id)
    elif action == 'revert':
        result = review.revert(program_id, user_id)
    else:
        return JsonResponse({'status': 'error', 'message': 'Неизвестное действие'}, status=400)

    if result.get('status') == 'locked':
        return JsonResponse(result, status=409)
    status_code = 200 if result.get('status') == 'success' else 400
    return JsonResponse(result, status=status_code)


@ajax_login_required
@review_api_access_required
@require_POST
def api_lock(request, program_id):
    """Захватить/продлить аренду карточки (TTL — constants.LOCK_TTL_MINUTES)."""
    review_item = repository.fetch_review_item(program_id)
    if review_item is None:
        return JsonResponse(
            {'status': 'error', 'message': 'Материал не найден в очереди'},
            status=404,
        )
    # Аренда нужна только для нерешённых карточек; историю можно смотреть
    # параллельно без блокировок.
    if review_item.get('status') != 'pending':
        return JsonResponse({'status': 'success', 'locked': False})
    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        payload = {}
    force = bool(payload.get('force')) and _is_chief_editor(request.user)
    result = repository.claim_review_lock(program_id, request.user.id, force=force)
    status_code = 200 if result.get('status') == 'success' else 409
    if result.get('status') == 'error':
        status_code = 500
    return JsonResponse(result, status=status_code)


@ajax_login_required
@review_api_access_required
@require_POST
def api_unlock(request, program_id):
    repository.release_review_lock(program_id, request.user.id)
    return JsonResponse({'status': 'success'})
