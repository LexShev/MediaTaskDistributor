"""Внешний HTTP-API Planner (server-to-server, без DRF).

Авторизация — статический токен в заголовке X-API-Key (env PUBLIC_API_TOKEN).
Дополнительно снаружи ограничиваем доступ по IP на уровне nginx.
"""

import os

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .program_info import get_program_payload

API_TOKEN = os.getenv('PUBLIC_API_TOKEN', 'secret_alex_test_oplan_token')


def _authorized(request):
    if not API_TOKEN:
        return False
    return request.headers.get('X-API-Key') == API_TOKEN


@require_GET
def program_detail(request, program_id):
    if not _authorized(request):
        return JsonResponse(
            {'status': 'error', 'code': 'unauthorized', 'message': 'Неверный API-ключ'},
            status=401,
        )
    status_code, payload = get_program_payload(program_id)
    return JsonResponse(payload, status=status_code)
