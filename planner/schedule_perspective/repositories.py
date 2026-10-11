"""Доступ к таблицам модуля перспективных сеток (БД Planner) + чтение Oplan3.

Простые операции идут через ORM. Рендер окна — одним raw-SQL запросом с
кросс-БД join'ом (`planner` + `oplan3`), чтобы не плодить N+1 на каждый слот.
"""

from django.db import connections, transaction
from django.utils import timezone

from planner.settings import PLANNER_DB

from schedule_perspective import constants
from schedule_perspective.models import (
    PerspectiveDay, PerspectiveNoMaterial, PerspectiveSlot,
)

# Смещение для безопасного пересчёта уникальных позиций одним шагом
# (в MSSQL UPDATE ... = position+1 по уникальному индексу может ловить
# транзиентный конфликт; двухшаговый сдвиг это исключает).
_OFFSET = 1_000_000


# --- Дни --------------------------------------------------------------------

def get_or_create_day(schedule_id, day_date):
    day, _ = PerspectiveDay.objects.get_or_create(
        schedule_id=schedule_id, day_date=day_date,
        defaults={'status': constants.STATUS_DRAFT},
    )
    return day


def fetch_days(schedule_id, start, end):
    """Период -> {date: day_info}."""
    result = {}
    for day in PerspectiveDay.objects.filter(
        schedule_id=schedule_id, day_date__gte=start, day_date__lte=end,
    ):
        result[day.day_date] = {
            'status': day.status,
            'approved_by': day.approved_by,
            'approved_at': day.approved_at,
            'final_by': day.final_by,
            'final_at': day.final_at,
        }
    return result


def set_status(schedule_id, dates, status, user_id):
    """Переводит перечисленные дни в новый статус (одной транзакцией)."""
    now = timezone.now()
    updated = 0
    with transaction.atomic():
        qs = PerspectiveDay.objects.filter(schedule_id=schedule_id, day_date__in=dates)
        values = {'status': status, 'updated_at': now}
        if status == constants.STATUS_CHIEF_APPROVED:
            values.update(approved_by=user_id, approved_at=now)
        elif status == constants.STATUS_FINAL_APPROVED:
            values.update(final_by=user_id, final_at=now)
        updated = qs.update(**values)
    return updated


# --- Позиции ----------------------------------------------------------------

def _day_max_position(schedule_id, day_date):
    from django.db.models import Max
    value = PerspectiveSlot.objects.filter(
        schedule_id=schedule_id, day_date=day_date,
    ).aggregate(m=Max('position'))['m']
    return value if value is not None else -1


def _shift_range(schedule_id, day_date, lo, hi, delta):
    """Сдвигает позиции в [lo, hi] на delta безопасно (двухшаговый offset)."""
    if hi < lo or delta == 0:
        return
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.perspective_slot SET position = position + %s
            WHERE schedule_id = %s AND day_date = %s AND position BETWEEN %s AND %s
            """,
            (_OFFSET, schedule_id, day_date, lo, hi),
        )
        cursor.execute(
            """
            UPDATE dbo.perspective_slot SET position = position - %s + %s
            WHERE schedule_id = %s AND day_date = %s AND position BETWEEN %s AND %s
            """,
            (_OFFSET, delta, schedule_id, day_date, lo + _OFFSET, hi + _OFFSET),
        )


def count_slots(schedule_id, day_date):
    return PerspectiveSlot.objects.filter(
        schedule_id=schedule_id, day_date=day_date,
    ).count()


def insert_slot(schedule_id, day_date, position, oplan_program_id=None,
                no_material_id=None, duration_frames=None):
    """Вставляет слот в позицию `position`, сдвигая последующие."""
    get_or_create_day(schedule_id, day_date)
    with transaction.atomic():
        _shift_range(schedule_id, day_date, position,
                     _day_max_position(schedule_id, day_date), 1)
        slot = PerspectiveSlot.objects.create(
            schedule_id=schedule_id,
            day_date=day_date,
            position=position,
            oplan_program_id=oplan_program_id,
            no_material_id=no_material_id,
            duration_frames=duration_frames,
        )
    return slot


def append_slot(schedule_id, day_date, oplan_program_id=None,
                no_material_id=None, duration_frames=None):
    position = _day_max_position(schedule_id, day_date) + 1
    return insert_slot(
        schedule_id, day_date, position,
        oplan_program_id=oplan_program_id,
        no_material_id=no_material_id,
        duration_frames=duration_frames,
    )


def delete_slot(slot_id):
    slot = PerspectiveSlot.objects.filter(id=slot_id).first()
    if not slot:
        return False
    with transaction.atomic():
        schedule_id, day_date, position = slot.schedule_id, slot.day_date, slot.position
        max_pos = _day_max_position(schedule_id, day_date)
        slot.delete()
        _shift_range(schedule_id, day_date, position + 1, max_pos, -1)
    return True


def move_slot(slot_id, to_day, to_position):
    """Перемещение без пересоздания строки (MSSQL IDENTITY не даёт явный PK)."""
    slot = PerspectiveSlot.objects.filter(id=slot_id).first()
    if not slot:
        return False
    src_day, src_position = slot.day_date, slot.position
    if src_day == to_day and src_position == to_position:
        return True
    schedule_id = slot.schedule_id
    to_position = max(0, to_position)
    sentinel = 2 * _OFFSET
    with transaction.atomic():
        src_max = _day_max_position(schedule_id, src_day)
        to_max = _day_max_position(schedule_id, to_day)
        # Выводим слот из пространства уникального индекса.
        slot.day_date = to_day
        slot.position = sentinel
        slot.save(update_fields=['day_date', 'position', 'updated_at'])

        if src_day != to_day:
            _shift_range(schedule_id, src_day, src_position + 1, src_max, -1)
            _shift_range(schedule_id, to_day, to_position, to_max, 1)
        elif to_position < src_position:
            _shift_range(schedule_id, src_day, to_position, src_position - 1, 1)
        else:  # to_position > src_position
            _shift_range(schedule_id, src_day, src_position + 1, to_position, -1)

        get_or_create_day(schedule_id, to_day)
        slot.position = to_position
        slot.save(update_fields=['position', 'updated_at'])
    return True


# --- Окно (рендер) ----------------------------------------------------------

_WINDOW_SQL = """
SELECT
    S.id, S.schedule_id, S.day_date, S.position,
    S.oplan_program_id, S.no_material_id, S.duration_frames,
    Op.program_kind AS op_kind, Op.episode_num AS op_episode, Op.name AS op_name,
    OpParent.name AS op_parent_name,
    FMI.has_file AS op_has_file, FMI.kinopoisk_id AS op_kp_id,
    NM.kind AS nm_kind, NM.kinopoisk_id AS nm_kp_id,
    NM.season_num AS nm_season, NM.episode_num AS nm_episode,
    NM.title AS nm_title
FROM dbo.perspective_slot AS S
LEFT JOIN [oplan3].dbo.program AS Op ON Op.program_id = S.oplan_program_id
LEFT JOIN [oplan3].dbo.program AS OpParent ON OpParent.program_id = Op.parent_id
LEFT JOIN dbo.film_material_index AS FMI ON FMI.oplan_program_id = S.oplan_program_id
LEFT JOIN dbo.perspective_no_material AS NM ON NM.id = S.no_material_id
WHERE S.schedule_id = %s
  AND S.day_date >= %s
  AND S.day_date <= %s
ORDER BY S.day_date, S.position
"""


def fetch_window(schedule_id, start, end):
    """Слоты окна с разрешёнными для отображения полями."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(_WINDOW_SQL, (schedule_id, start, end))
        rows = cursor.fetchall()
    columns = (
        'id', 'schedule_id', 'day_date', 'position',
        'oplan_program_id', 'no_material_id', 'duration_frames',
        'op_kind', 'op_episode', 'op_name', 'op_parent_name',
        'op_has_file', 'op_kp_id',
        'nm_kind', 'nm_kp_id', 'nm_season', 'nm_episode', 'nm_title',
    )
    slots = []
    for row in rows:
        item = dict(zip(columns, row))
        if item['oplan_program_id']:
            kind = item['op_kind']
            title = item['op_parent_name'] if kind == constants.EPISODE_KIND else item['op_name']
            season_num = None
            episode_num = item['op_episode']
            in_base = bool(item['op_has_file'])
            kp_id = item['op_kp_id']
        else:
            kind = item['nm_kind']
            title = item['nm_title']
            season_num = item['nm_season']
            episode_num = item['nm_episode']
            in_base = False
            kp_id = item['nm_kp_id']
        slots.append({
            'id': item['id'],
            'schedule_id': item['schedule_id'],
            'day_date': item['day_date'].isoformat(),
            'position': item['position'],
            'oplan_program_id': item['oplan_program_id'],
            'no_material_id': item['no_material_id'],
            'kind': kind,
            'title': title or 'Без названия',
            'season_num': season_num,
            'episode_num': episode_num,
            'duration_frames': item['duration_frames'],
            'in_base': in_base,
            'kinopoisk_id': kp_id,
        })
    return slots


# --- Узлы отсутствующих материалов ------------------------------------------

def _find_node(kind, kinopoisk_id, parent_id, season_num, episode_num):
    qs = PerspectiveNoMaterial.objects.filter(
        kind=kind, kinopoisk_id=kinopoisk_id,
        parent_id=parent_id, season_num=season_num, episode_num=episode_num,
    )
    return qs.first()


def get_or_create_node(kind, kinopoisk_id, title=None, parent_id=None,
                       season_num=None, episode_num=None):
    node = _find_node(kind, kinopoisk_id, parent_id, season_num, episode_num)
    if node:
        if title and not node.title:
            node.title = title
            node.save(update_fields=['title', 'updated_at'])
        return node
    return PerspectiveNoMaterial.objects.create(
        kind=kind, kinopoisk_id=kinopoisk_id, title=title,
        parent_id=parent_id, season_num=season_num, episode_num=episode_num,
    )


def get_or_create_series_tree(kinopoisk_id, title, season_num, episode_num):
    """Возвращает узел серии (kind=3), создавая корень (1) и сезон (4) при необходимости."""
    root = get_or_create_node(
        constants.CATALOG_KIND, kinopoisk_id, title=title,
    )
    season = get_or_create_node(
        constants.SEASON_KIND, kinopoisk_id, title=title,
        parent_id=root.id, season_num=season_num,
    )
    episode = get_or_create_node(
        constants.EPISODE_KIND, kinopoisk_id, title=title,
        parent_id=season.id, season_num=season_num, episode_num=episode_num,
    )
    return episode


def get_or_create_film_node(kinopoisk_id, title):
    return get_or_create_node(
        constants.FILM_KIND, kinopoisk_id, title=title,
    )


def is_no_material_slot_owner(node_id):
    return PerspectiveSlot.objects.filter(no_material_id=node_id).exists()


def get_oplan_duration_frames(program_id):
    """Длительность в кадрах из Oplan3 (или None)."""
    if not program_id:
        return None
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute(
                "SELECT duration FROM [oplan3].dbo.program WHERE program_id = %s",
                (program_id,),
            )
            row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else None
    except Exception as error:
        print('schedule_perspective oplan duration error:', error)
        return None


def day_total_frames(schedule_id, day_date):
    """Сумма длительностей слотов дня (null -> дефолт)."""
    from django.db.models import Sum
    total = PerspectiveSlot.objects.filter(
        schedule_id=schedule_id, day_date=day_date,
    ).aggregate(total=Sum('duration_frames'))['total']
    if total:
        return int(total)
    # Учесть слоты без снапшота как дефолт.
    null_count = PerspectiveSlot.objects.filter(
        schedule_id=schedule_id, day_date=day_date, duration_frames__isnull=True,
    ).count()
    return null_count * constants.DEFAULT_DURATION_FRAMES
