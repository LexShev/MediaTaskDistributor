"""HTTP-эндпоинты модуля перспективных сеток."""

import json
from datetime import date, timedelta
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from main.decorators import ajax_login_required
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings

from schedule_perspective import (
    catalog, cinemaatlas, constants, export, metadata, repositories, roles, statuses,
)


# --- Страница -----------------------------------------------------------------

def _parse_start(value):
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    today = date.today()
    return today - timedelta(days=today.weekday())


def _get_channel(request):
    try:
        channel = int(request.GET.get('channel') or 3)
    except (TypeError, ValueError):
        channel = 3
    if channel not in constants.CHANNELS:
        channel = 3
    return channel


def _get_days(request):
    try:
        days = int(request.GET.get('days') or constants.DEFAULT_WINDOW_DAYS)
    except (TypeError, ValueError):
        days = constants.DEFAULT_WINDOW_DAYS
    if days not in constants.ALLOWED_WINDOW_DAYS:
        days = constants.DEFAULT_WINDOW_DAYS
    return days


def schedule_perspective(request):
    if not roles.can_view(request.user):
        return HttpResponseForbidden('Недостаточно прав для просмотра перспективных сеток')
    data = {
        'channels': constants.CHANNELS,
        'default_channel': _get_channel(request),
        'default_start': _parse_start(request.GET.get('start')).isoformat(),
        'default_days': _get_days(request),
        'allowed_days': constants.ALLOWED_WINDOW_DAYS,
        'can_edit': roles.can_edit(request.user),
        'permissions': ask_db_permissions(request.user.id),
        'tabs': get_main_settings().get_header_panels(
            request.user.groups.first().id if request.user.groups.exists() else None),
    }
    return render(request, 'schedule_perspective/index.html', data)


# --- Окно ---------------------------------------------------------------------

def _repeats(slots):
    counts = {}
    for slot in slots:
        key = (slot['oplan_program_id'] or slot['kinopoisk_id'],
               slot['season_num'], slot['episode_num'])
        counts[key] = counts.get(key, 0) + 1
    for slot in slots:
        key = (slot['oplan_program_id'] or slot['kinopoisk_id'],
               slot['season_num'], slot['episode_num'])
        slot['is_repeat'] = counts.get(key, 0) > 1


@ajax_login_required
def api_window(request):
    if not roles.can_view(request.user):
        return JsonResponse({'status': 'error', 'message': 'Нет доступа'}, status=403)
    channel = _get_channel(request)
    days = _get_days(request)
    start = _parse_start(request.GET.get('start'))
    end = start + timedelta(days=days - 1)

    slots = repositories.fetch_window(channel, start, end)
    _repeats(slots)
    day_status = repositories.fetch_days(channel, start, end)

    slots_by_day = {}
    for slot in slots:
        slots_by_day.setdefault(slot['day_date'], []).append(slot)

    day_list = []
    for offset in range(days):
        day = (start + timedelta(days=offset))
        key = day.isoformat()
        day_slots = slots_by_day.get(key, [])
        total_frames = sum(s['duration_frames'] or constants.DEFAULT_DURATION_FRAMES
                           for s in day_slots)
        status = day_status.get(day, {}).get('status', constants.STATUS_DRAFT)
        day_list.append({
            'date': key,
            'status': status,
            'slots': day_slots,
            'total_frames': total_frames,
            'total_hours': round(total_frames / constants.FPS / 3600, 2),
        })

    return JsonResponse({
        'status': 'success',
        'channel': channel,
        'channel_name': constants.CHANNELS.get(channel, str(channel)),
        'start': start.isoformat(),
        'days': days,
        'target_hours': constants.DAY_TARGET_HOURS.get(channel, 8),
        'can_edit': roles.can_edit(request.user),
        'fps': constants.FPS,
        'default_duration_frames': constants.DEFAULT_DURATION_FRAMES,
        'day_list': day_list,
    })


# --- Поиск --------------------------------------------------------------------

@ajax_login_required
def api_search(request):
    query = request.GET.get('q') or ''
    return JsonResponse({'status': 'success', 'items': catalog.search(query)})


@ajax_login_required
def api_series_structure(request, kinopoisk_id):
    return JsonResponse({'status': 'success',
                         'structure': catalog.get_series_structure(kinopoisk_id)})


# --- Метаданные ---------------------------------------------------------------

@ajax_login_required
def api_film_info(request):
    kp_raw = request.GET.get('kp_ids') or ''
    op_raw = request.GET.get('oplan_ids') or ''
    kp_ids = [int(x) for x in kp_raw.split(',') if x.strip().isdigit()]
    oplan_ids = [int(x) for x in op_raw.split(',') if x.strip().isdigit()]
    return JsonResponse({
        'status': 'success',
        'kinopoisk': metadata.get_film_metadata(kp_ids),
        'oplan': metadata.get_oplan_metadata(oplan_ids),
    })


# --- Слоты --------------------------------------------------------------------

def _payload(request):
    try:
        return json.loads(request.body or '{}')
    except ValueError:
        return None


def _edit_guard(request):
    if not roles.can_edit(request.user):
        return JsonResponse({'status': 'error', 'message': 'Правка доступна только редактору или администратору'},
                            status=403)
    return None


def _build_episodes(payload):
    """Список серий для раскладки: in-base (Oplan) или отсутствующие."""
    kp_id = int(payload['kinopoisk_id'])
    season_num = int(payload.get('season_num') or 1)
    episode_from = int(payload.get('episode_from') or 1)
    episode_to = int(payload.get('episode_to') or episode_from)
    if episode_to < episode_from:
        episode_from, episode_to = episode_to, episode_from
    title = payload.get('title') or ''

    structure = catalog.get_series_structure(kp_id)
    if structure['seasons']:
        # in-base: берём сезон по позиции (1-based) или единственный
        index = max(0, min(len(structure['seasons']) - 1, season_num - 1))
        season = structure['seasons'][index]
        episodes = []
        for ep in season['episodes']:
            num = ep.get('episode_num')
            if num is None or episode_from <= num <= episode_to:
                episodes.append({
                    'oplan_program_id': ep['oplan_program_id'],
                    'no_material_id': None,
                    'season_num': season_num,
                    'episode_num': num if num is not None else episode_from + len(episodes),
                    'duration_frames': ep.get('duration') or constants.DEFAULT_DURATION_FRAMES,
                })
        return episodes

    # отсутствует в базе: создаём узлы
    base_duration = catalog.get_duration_frames(kp_id)
    episodes = []
    for num in range(episode_from, episode_to + 1):
        node = repositories.get_or_create_series_tree(kp_id, title, season_num, num)
        episodes.append({
            'oplan_program_id': None,
            'no_material_id': node.id,
            'season_num': season_num,
            'episode_num': num,
            'duration_frames': base_duration,
        })
    return episodes


def _distribute(episodes, channel, start_day, start_position):
    """Раскладка серий: с явной позиции дня, при переполнении — в конец след. дней.

    Позиции не сдвигаются: для каждой серии берём ближайшую свободную позицию.
    """
    target_frames = constants.DAY_TARGET_HOURS.get(channel, 8) * 3600 * constants.FPS
    day = start_day
    next_position = start_position  # None -> ставить в конец дня
    current_frames = repositories.day_total_frames(channel, day)
    created = 0
    for episode in episodes:
        frames = episode['duration_frames'] or constants.DEFAULT_DURATION_FRAMES
        if current_frames > 0 and current_frames + frames > target_frames:
            day = day + timedelta(days=1)
            next_position = None
            current_frames = repositories.day_total_frames(channel, day)
        occupied = repositories.occupied_positions(channel, day)
        if next_position is None:
            position = (max(occupied) + 1) if occupied else 0
        else:
            position = next_position
            while position in occupied:
                position += 1
        repositories.insert_slot(
            channel, day, position,
            oplan_program_id=episode['oplan_program_id'],
            no_material_id=episode['no_material_id'], duration_frames=frames)
        next_position = position + 1
        current_frames += frames
        created += 1
    return created


@ajax_login_required
@require_POST
def api_slot_add(request):
    guard = _edit_guard(request)
    if guard:
        return guard
    payload = _payload(request)
    if not payload:
        return JsonResponse({'status': 'error', 'message': 'Некорректный запрос'}, status=400)
    try:
        channel = int(payload['channel'])
        day = date.fromisoformat(payload['day'])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Некорректный канал/дата'}, status=400)
    position = None
    if payload.get('position') is not None:
        position = int(payload['position'])

    kind = payload.get('kind') or 'film'
    try:
        if kind == 'film':
            oplan_program_id = payload.get('oplan_program_id')
            kp_id = payload.get('kinopoisk_id')
            frames = (repositories.get_oplan_duration_frames(oplan_program_id)
                      if oplan_program_id else catalog.get_duration_frames(kp_id))
            frames = frames or constants.DEFAULT_DURATION_FRAMES
            if oplan_program_id:
                if position is None:
                    repositories.append_slot(channel, day, oplan_program_id=oplan_program_id,
                                             duration_frames=frames)
                else:
                    repositories.insert_slot(channel, day, position,
                                             oplan_program_id=oplan_program_id,
                                             duration_frames=frames)
            else:
                node = repositories.get_or_create_film_node(kp_id, payload.get('title') or '')
                if position is None:
                    repositories.append_slot(channel, day, no_material_id=node.id,
                                             duration_frames=frames)
                else:
                    repositories.insert_slot(channel, day, position, no_material_id=node.id,
                                             duration_frames=frames)
            return JsonResponse({'status': 'success', 'created': 1})

        if kind == 'series':
            episodes = _build_episodes(payload)
            if not episodes:
                return JsonResponse({'status': 'error', 'message': 'Не найдено серий для вставки'},
                                    status=400)
            # Вся раскладка — одной транзакцией, чтобы блокировка одного из
            # последующих дней не оставила частично вставленный диапазон.
            with transaction.atomic():
                created = _distribute(episodes, channel, day, position)
            return JsonResponse({'status': 'success', 'created': created})
    except repositories.DayNotEditable as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=403)
    except repositories.PositionTaken as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=409)

    return JsonResponse({'status': 'error', 'message': 'Неизвестный вид материала'}, status=400)


@ajax_login_required
@require_POST
def api_slot_move(request):
    guard = _edit_guard(request)
    if guard:
        return guard
    payload = _payload(request) or {}
    try:
        slot_id = int(payload['slot_id'])
        to_day = date.fromisoformat(payload['day'])
        to_position = int(payload['position'])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Некорректные параметры'}, status=400)
    try:
        ok = repositories.move_slot(slot_id, to_day, to_position)
    except repositories.DayNotEditable as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=403)
    return JsonResponse({'status': 'success' if ok else 'error'})


@ajax_login_required
@require_POST
def api_slot_delete(request):
    guard = _edit_guard(request)
    if guard:
        return guard
    payload = _payload(request) or {}
    try:
        slot_id = int(payload['slot_id'])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Некорректный слот'}, status=400)
    try:
        ok = repositories.delete_slot(slot_id)
    except repositories.DayNotEditable as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=403)
    return JsonResponse({'status': 'success' if ok else 'error'})


# --- Статусы ------------------------------------------------------------------

def _dates(payload):
    raw = payload.get('dates')
    if isinstance(raw, list):
        return [date.fromisoformat(d) for d in raw]
    if isinstance(raw, str) and raw:
        return [date.fromisoformat(raw)]
    return []


@ajax_login_required
@require_POST
def api_day_status(request, action):
    guard = _edit_guard(request)
    if guard:
        return guard
    payload = _payload(request) or {}
    try:
        channel = int(payload['channel'])
        dates = _dates(payload)
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Некорректные параметры'}, status=400)
    handlers = {
        'approve': statuses.approve,
        'finalize': statuses.finalize,
        'reopen': statuses.reopen,
    }
    handler = handlers.get(action)
    if handler is None:
        return JsonResponse({'status': 'error', 'message': 'Неизвестное действие'}, status=400)
    result = handler(channel, dates, request.user.id)
    return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)


# --- Скачивание (имитация) ----------------------------------------------------

@ajax_login_required
@require_POST
def api_generate_downloads(request):
    guard = _edit_guard(request)
    if guard:
        return guard
    payload = _payload(request) or {}
    try:
        channel = int(payload['channel'])
        day = date.fromisoformat(payload['day'])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Некорректные параметры'}, status=400)
    return JsonResponse(cinemaatlas.create_download_task(channel, day))


# --- Экспорт в Excel ----------------------------------------------------------

@login_required()
def schedule_perspective_export(request):
    """Выгрузка текущего окна в .xlsx (данные читаются напрямую из БД)."""
    if not roles.can_view(request.user):
        return HttpResponseForbidden('Недостаточно прав для экспорта')
    channel = _get_channel(request)
    days = _get_days(request)
    start = _parse_start(request.GET.get('start'))
    end = start + timedelta(days=days - 1)

    slots = repositories.fetch_window(channel, start, end)
    content = export.build_schedule_workbook(channel, start, days, slots)

    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    channel_name = constants.CHANNELS.get(channel, str(channel))
    filename = f'Сетка_{channel_name}_{start:%Y-%m-%d}_{days}дн.xlsx'
    response['Content-Disposition'] = (
        'attachment; filename="schedule.xlsx"; '
        f"filename*=UTF-8''{quote(filename)}"
    )
    return response
