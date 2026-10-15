"""Данные Oplan3 по одному program_id для внешнего HTTP-API.

Слои разделены намеренно:
    fetch_program        — только БД, отдаёт «сырой» словарь колонок;
    detect_object_type   — чистый маппинг program_type_id/program_kind -> тип;
    serialize_program    — чистый сборщик JSON-объекта по единой схеме;
    get_program_payload  — оркестрация + HTTP-код и конверт ошибки.

Oplan3 — read-only. Удаление (deleted/DeletedIncludeParent) НЕ фильтруется в
SQL: строку читаем целиком и решаем на уровне выше, чтобы вернуть 410.
"""

from django.db import connections

from planner.settings import OPLAN_DB

# program_type_id -> семейство. Сериальное семейство включает цензурные и
# субтитровые варианты, короткометражки (16/20) отнесены к нему же — как
# принято в проекте (film_index/constants.py). Служебные типы не описаны.
TYPE_FAMILY = {
    4: 'series', 8: 'series', 12: 'series', 16: 'series', 20: 'series',
    5: 'film', 6: 'film', 7: 'film', 10: 'film', 11: 'film', 19: 'film',
}
# program_kind серии (родитель — родитель сезона/сериала, kind=4).
EPISODE_KIND = 3


def fetch_program(program_id):
    """Сырая строка program по program_id (включая deleted-флаги) или None.

    Родитель подтягивается self-join'ом: серия/сезон наследуют от него
    Season/EpisodesTotal. Псевдонимы колонок заданы в SELECT, ключи словаря
    берём из cursor.description — отдельный синхронный список не нужен.
    """
    query = f'''
        SELECT
            p.[program_id],
            p.[parent_id],
            p.[program_kind],
            p.[program_type_id],
            p.[name],
            p.[orig_name],
            p.[production_year],
            p.[production_country],
            p.[Director],
            p.[Cast],
            p.[Season],
            p.[episode_num],
            p.[EpisodesTotal],
            p.[duration],
            p.[annotation],
            p.[deleted],
            p.[DeletedIncludeParent],
            a.[Name] AS adult_type_name,
            parent.[name] AS parent_name,
            parent.[Season] AS parent_season,
            parent.[EpisodesTotal] AS parent_episodes_total
        FROM [{OPLAN_DB}].[dbo].[program] AS p
        LEFT JOIN [{OPLAN_DB}].[dbo].[program] AS parent
            ON parent.[program_id] = p.[parent_id]
        LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS a
            ON a.[AdultTypeID] = p.[AdultTypeID]
        WHERE p.[program_id] = %s
    '''
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(query, (program_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def detect_object_type(program_kind, program_type_id):
    """film | series | episode | unknown.

    Семейство — по program_type_id (спорные материалы, внесённые частями,
    попадают в сериальную группу независимо от kind), структура — по kind.
    """
    family = TYPE_FAMILY.get(program_type_id)
    if family == 'series':
        return 'episode' if program_kind == EPISODE_KIND else 'series'
    return family or 'unknown'


def serialize_program(row):
    """Собирает объект ответа по единой схеме: все ключи присутствуют всегда.

    Season валиден только у сезона; у серии наследуется от родителя.
    EpisodesTotal у серии всегда берётся от родителя — своё значение
    устаревшее и неактуальное.
    """
    object_type = detect_object_type(row.get('program_kind'), row.get('program_type_id'))
    season = row.get('Season')
    if season is None:
        season = row.get('parent_season')
    if object_type == 'episode':
        episodes_total = row.get('parent_episodes_total')
    else:
        episodes_total = row.get('EpisodesTotal')
    return {
        'type': object_type,
        'oplan_program_id': row.get('program_id'),
        'title': row.get('name'),
        'original_title': row.get('orig_name'),
        'year': row.get('production_year'),
        'country': row.get('production_country'),
        'director': row.get('Director'),
        'cast': row.get('Cast'),
        'age_rating': row.get('adult_type_name'),
        'description': row.get('annotation'),
        'duration_frames': row.get('duration'),
        'episodes_total': episodes_total,
        'parent_title': row.get('parent_name'),
        'season': season,
        'episode': row.get('episode_num'),
    }


def get_program_payload(program_id):
    """Возвращает (http_status, envelope) для вьюхи."""
    row = fetch_program(program_id)
    if row is None:
        return 404, {'status': 'error', 'code': 'not_found', 'message': 'Материал не найден'}
    if row.get('deleted') or row.get('DeletedIncludeParent'):
        return 410, {'status': 'error', 'code': 'deleted', 'message': 'Материал удалён в Oplan3'}
    return 200, {'status': 'success', 'object': serialize_program(row)}
