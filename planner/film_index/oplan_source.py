"""Источник данных Oplan3: материалы, наличие файла и длительность.

Oplan3 - только чтение. Здесь собираем «материальные» строки program
(фильмы + родители сезонов/сериалов + серии) вместе с признаком наличия
физического файла (JOIN File -> Clip -> program) и длительностью в кадрах.
"""

from django.db import connections

from planner.settings import OPLAN_DB
from film_index import constants


def _int_list(values) -> str:
    return ', '.join(str(int(value)) for value in values)


_FILE_EXISTS_SUBQUERY = f"""
    SELECT DISTINCT Progs2.[program_id]
    FROM [{OPLAN_DB}].[dbo].[File] AS Files
    JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
        ON Files.[ClipID] = Clips.[ClipID]
    JOIN [{OPLAN_DB}].[dbo].[program] AS Progs2
        ON Clips.[MaterialID] = Progs2.[SuitableMaterialForScheduleID]
    WHERE Files.[Deleted] = 0
      AND Files.[PhysicallyDeleted] = 0
      AND Clips.[Deleted] = 0
"""


def fetch_materials() -> list:
    """Возвращает материалы Oplan3 для индексации.

    Каждая строка: program_id, parent_id, program_kind, program_type_id,
    name, orig_name, production_year, production_country, director,
    duration (кадры), has_file.
    """
    query = f"""
    SELECT
        Progs.[program_id],
        Progs.[parent_id],
        Progs.[program_kind],
        Progs.[program_type_id],
        Progs.[name],
        Progs.[orig_name],
        Progs.[production_year],
        Progs.[production_country],
        Progs.[Director],
        Progs.[duration],
        CASE WHEN MatFiles.[program_id] IS NULL THEN 0 ELSE 1 END AS has_file
    FROM [{OPLAN_DB}].[dbo].[program] AS Progs
    LEFT JOIN ({_FILE_EXISTS_SUBQUERY}) AS MatFiles
        ON MatFiles.[program_id] = Progs.[program_id]
    WHERE Progs.[deleted] = 0
      AND Progs.[DeletedIncludeParent] = 0
      AND Progs.[program_type_id] IN ({_int_list(constants.ALLOWED_TYPES)})
      AND Progs.[program_kind] IN ({_int_list(constants.INDEX_KINDS)})
    """
    columns = (
        'program_id', 'parent_id', 'program_kind', 'program_type_id',
        'name', 'orig_name', 'production_year', 'production_country',
        'director', 'duration', 'has_file',
    )
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def fetch_match_targets() -> list:
    """Лёгкий запрос только для сопоставления (без JOIN по файлам).

    Возвращает фильмы и родителей сезонов/сериалов - то, что сопоставляется
    с каталогом Кинопоиска.
    """
    query = f"""
    SELECT
        Progs.[program_id],
        Progs.[parent_id],
        Progs.[program_kind],
        Progs.[program_type_id],
        Progs.[name],
        Progs.[orig_name],
        Progs.[production_year],
        Progs.[production_country],
        Progs.[Director]
    FROM [{OPLAN_DB}].[dbo].[program] AS Progs
    WHERE Progs.[deleted] = 0
      AND Progs.[DeletedIncludeParent] = 0
      AND Progs.[program_type_id] IN ({_int_list(constants.ALLOWED_TYPES)})
      AND Progs.[program_kind] IN ({_int_list(constants.MATCH_KINDS)})
    """
    columns = (
        'program_id', 'parent_id', 'program_kind', 'program_type_id',
        'name', 'orig_name', 'production_year', 'production_country',
        'director',
    )
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return [
        material for material in (dict(zip(columns, row)) for row in rows)
        if _is_real_material(material)
    ]


def _is_real_material(material: dict) -> bool:
    name = (material.get('name') or '').strip()
    return name not in constants.SERVICE_NAMES


def is_match_target(material: dict) -> bool:
    """Строка, которую сопоставляем с каталогом Кинопоиска.

    Фильмы и родители (сезоны/сериалы). Серии не матчатся - наследуют
    kinopoisk_id родителя.
    """
    if material.get('program_kind') not in constants.MATCH_KINDS:
        return False
    return _is_real_material(material)


def duration_frames(material: dict):
    """Длительность в кадрах из Oplan3 - только при наличии файла."""
    if material.get('has_file'):
        value = material.get('duration')
        return int(value) if value is not None else None
    return None


def fetch_material(program_id) -> dict:
    """Снимок одного материала Oplan3 (для карточки разбора)."""
    query = f"""
    SELECT
        Progs.[program_id], Progs.[parent_id], Progs.[program_kind],
        Progs.[program_type_id], Progs.[name], Progs.[orig_name],
        Progs.[production_year], Progs.[production_country], Progs.[Director],
        Progs.[episode_num], Progs.[duration],
        CASE WHEN MatFiles.[program_id] IS NULL THEN 0 ELSE 1 END AS has_file
    FROM [{OPLAN_DB}].[dbo].[program] AS Progs
    LEFT JOIN ({_FILE_EXISTS_SUBQUERY}) AS MatFiles
        ON MatFiles.[program_id] = Progs.[program_id]
    WHERE Progs.[program_id] = %s
    """
    columns = (
        'program_id', 'parent_id', 'program_kind', 'program_type_id',
        'name', 'orig_name', 'production_year', 'production_country',
        'director', 'episode_num', 'duration', 'has_file',
    )
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(query, (program_id,))
        row = cursor.fetchone()
    if not row:
        return None
    return dict(zip(columns, row))


def fetch_description(program_id):
    """Краткое описание (ProgramCustomFieldId = 5)."""
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT [TextValue] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
            WHERE [ObjectId] = %s AND [ProgramCustomFieldId] = 5
            """,
            (program_id,),
        )
        row = cursor.fetchone()
    return row[0] if row else None


def fetch_descriptions(program_ids) -> dict:
    """Батч кратких описаний: program_id -> TextValue."""
    program_ids = list(program_ids)
    if not program_ids:
        return {}
    result = {}
    chunk = 500
    with connections[OPLAN_DB].cursor() as cursor:
        for start in range(0, len(program_ids), chunk):
            batch = program_ids[start:start + chunk]
            placeholders = ', '.join(['%s'] * len(batch))
            cursor.execute(
                f"""
                SELECT [ObjectId], [TextValue]
                FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 5
                  AND [ObjectId] IN ({placeholders})
                """,
                batch,
            )
            for program_id, text in cursor.fetchall():
                if text:
                    result[program_id] = text
    return result
