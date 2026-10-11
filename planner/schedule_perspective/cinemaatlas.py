"""Адаптер задач на скачивание в CinemaAtlas (имитация).

Задача = (канал + день). Реальный вызов CA не делаем — только формируем
список и логируем. Позже интерфейс заменяется на общую очередь jobs без
изменения вызывающего кода.
"""

from django.db import connections

from planner.settings import PLANNER_DB

from schedule_perspective import constants

_SQL = """
SELECT S.id, S.oplan_program_id, S.no_material_id,
       NM.kinopoisk_id AS nm_kp_id,
       FMI.kinopoisk_id AS op_kp_id, FMI.has_file
FROM dbo.perspective_slot AS S
LEFT JOIN dbo.film_material_index AS FMI ON FMI.oplan_program_id = S.oplan_program_id
LEFT JOIN dbo.perspective_no_material AS NM ON NM.id = S.no_material_id
WHERE S.schedule_id = %s AND S.day_date = %s
ORDER BY S.position
"""


def build_download_items(schedule_id, day_date):
    """Список kinopoisk_id материалов дня, которых нет в базе."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(_SQL, (schedule_id, day_date))
        rows = cursor.fetchall()
    items = []
    seen = set()
    for _slot_id, oplan_program_id, no_material_id, nm_kp_id, op_kp_id, has_file in rows:
        missing = no_material_id is not None or not has_file
        if not missing:
            continue
        kp_id = nm_kp_id if no_material_id is not None else op_kp_id
        if kp_id and kp_id not in seen:
            seen.add(kp_id)
            items.append(kp_id)
    return items


def create_download_task(schedule_id, day_date):
    """Имитация постановки задачи в CA: канал + день."""
    channel = constants.CHANNELS.get(schedule_id, str(schedule_id))
    task_name = f'{channel} — {day_date}'
    items = build_download_items(schedule_id, day_date)
    print(f'[CA/имитация] задача «{task_name}», позиций: {len(items)}')
    return {
        'status': 'success',
        'task_name': task_name,
        'items': items,
        'count': len(items),
        'imitation': True,
    }
