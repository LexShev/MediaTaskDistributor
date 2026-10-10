"""Веб-интерфейс ручного разбора сопоставления film_index."""

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from main.decorators import ajax_login_required
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from film_index import repository, review
from film_index.oplan_source import fetch_description, fetch_material
from film_index.posters import get_poster
from film_index.search import search_catalog


@login_required()
def review_page(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    data = {
        'stats': repository.review_stats(),
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group),
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
    items = repository.fetch_review_queue(
        status=request.GET.get('status') or 'pending',
        bucket=request.GET.get('bucket') or None,
        kind=kind,
        parent_id=parent_id,
        name=request.GET.get('name') or None,
        limit=int(request.GET.get('limit') or 500),
        offset=int(request.GET.get('offset') or 0),
    )
    return JsonResponse({'status': 'success', 'items': items, 'count': len(items)})


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
    return JsonResponse({
        'status': 'success',
        'material': material,
        'description': fetch_description(program_id),
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
def api_poster(request):
    kp_id = (request.GET.get('kp_id') or '').strip()
    if not kp_id.isdigit():
        return HttpResponse(status=404)
    content, content_type = get_poster(int(kp_id))
    if content is None:
        return HttpResponse(status=404)
    response = HttpResponse(content, content_type=content_type)
    response['Cache-Control'] = 'public, max-age=2592000'
    return response


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
