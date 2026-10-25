"""Веб-интерфейс ручного разбора сопоставления film_index."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from main.decorators import ajax_login_required
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from film_index import constants, repository, review
from film_index.oplan_source import fetch_description, fetch_material
from film_index.search import search_catalog


@login_required()
def review_page(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    data = {
        'stats': repository.review_stats(),
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group),
        'fps': constants.FPS,
    }
    return render(request, 'film_index/review.html', data)


@ajax_login_required
def api_queue(request):
    kind = request.GET.get('kind') or None
    parent_id = request.GET.get('parent_id')
    try:
        parent_id = int(parent_id) if parent_id not in (None, '') else None
    except ValueError:
        parent_id = None
    status = request.GET.get('status') or 'pending'
    bucket = request.GET.get('bucket') or None
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
        limit=limit,
        offset=offset,
    )
    total = repository.count_review_queue(
        status=status,
        bucket=bucket,
        kind=kind,
        parent_id=parent_id,
        name=name,
    )
    return JsonResponse({
        'status': 'success', 'items': items, 'count': len(items),
        'total': total, 'offset': offset, 'limit': limit,
    })


@ajax_login_required
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
def api_search(request):
    query = request.GET.get('q') or ''
    return JsonResponse({'status': 'success', 'items': search_catalog(query)})


@ajax_login_required
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
        result = review.revert(program_id)
    else:
        return JsonResponse({'status': 'error', 'message': 'Неизвестное действие'}, status=400)

    status_code = 200 if result.get('status') == 'success' else 400
    return JsonResponse(result, status=status_code)
