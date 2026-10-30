"""Запись результатов film_index в БД Planner."""

import json

from django.db import IntegrityError, connections, transaction

from planner.settings import OPLAN_DB, PLANNER_DB
from film_index import constants


def _int_list(values) -> str:
    return ', '.join(str(int(value)) for value in values)


# --- Прогоны ---------------------------------------------------------------

def create_run(run_id, mode, sample_size=None, total_targets=None) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dbo.film_match_run (id, mode, sample_size, total_targets)
            VALUES (%s, %s, %s, %s)
            """,
            (str(run_id), mode, sample_size, total_targets),
        )


def finish_run(run_id, counts: dict, notes: str = None) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.film_match_run
            SET finished_at = SYSDATETIME(),
                auto_high = %s, band = %s, ambiguous = %s, unmatched = %s,
                notes = %s
            WHERE id = %s
            """,
            (
                counts.get('auto_high'), counts.get('band'),
                counts.get('ambiguous'), counts.get('unmatched'),
                notes, str(run_id),
            ),
        )


# --- film_material_index ---------------------------------------------------

def upsert_index(rows: list) -> None:
    """rows: (oplan_program_id, kinopoisk_id, has_file, duration_frames, match_source).

    Ручные сопоставления (match_source='manual') не перетираются: обновляются
    только has_file/duration, а kinopoisk_id/match_source сохраняются.
    """
    if not rows:
        return
    statement = """
    MERGE dbo.film_material_index AS target
    USING (SELECT %s AS oplan_program_id, %s AS kinopoisk_id, %s AS has_file,
                  %s AS duration_frames, %s AS match_source) AS source
    ON target.oplan_program_id = source.oplan_program_id
    WHEN MATCHED THEN UPDATE SET
        target.kinopoisk_id = CASE WHEN target.match_source = 'manual'
                                   THEN target.kinopoisk_id ELSE source.kinopoisk_id END,
        target.match_source  = CASE WHEN target.match_source = 'manual'
                                   THEN target.match_source ELSE source.match_source END,
        target.has_file = source.has_file,
        target.duration_frames = source.duration_frames,
        target.refreshed_at = SYSDATETIME()
    WHEN NOT MATCHED THEN INSERT
        (oplan_program_id, kinopoisk_id, has_file, duration_frames, match_source)
        VALUES (source.oplan_program_id, source.kinopoisk_id,
                source.has_file, source.duration_frames, source.match_source);
    """
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.executemany(statement, rows)


def load_manual_matches() -> dict:
    """program_id -> kinopoisk_id для ручных сопоставлений."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            SELECT oplan_program_id, kinopoisk_id
            FROM dbo.film_material_index
            WHERE match_source = 'manual' AND kinopoisk_id IS NOT NULL
            """
        )
        return {row[0]: row[1] for row in cursor.fetchall()}


# --- film_match_review -----------------------------------------------------

def reset_pending_review() -> None:
    """Очищает очередь pending перед новым прогоном (resolved/rejected остаются)."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute("DELETE FROM dbo.film_match_review WHERE status = 'pending'")
        cursor.execute("DELETE FROM dbo.film_review_lock")


def load_excluded_review_ids() -> set:
    """program_id, уже решённые вручную или отклонённые (повторно не ставим)."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            SELECT oplan_program_id FROM dbo.film_match_review
            WHERE status IN ('resolved', 'rejected')
            """
        )
        return {row[0] for row in cursor.fetchall()}


def insert_staging(rows: list) -> None:
    """rows: (run_id, oplan_program_id, candidate_kp_id, score, title_score,
    year_score, country_score, bucket, reason)."""
    if not rows:
        return
    statement = """
    INSERT INTO dbo.film_match_staging
        (run_id, oplan_program_id, candidate_kp_id, score,
         title_score, year_score, country_score, bucket, reason)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    normalized = [(str(row[0]),) + tuple(row[1:]) for row in rows]
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.executemany(statement, normalized)


def insert_review(rows: list) -> None:
    """rows: (oplan_program_id, run_id, candidates(list), bucket, status)."""
    if not rows:
        return
    statement = """
    INSERT INTO dbo.film_match_review
        (oplan_program_id, run_id, candidates_json, bucket, status)
    VALUES (%s, %s, %s, %s, %s)
    """
    normalized = [
        (oplan_program_id, str(run_id),
         json.dumps(candidates, ensure_ascii=False), bucket, status)
        for oplan_program_id, run_id, candidates, bucket, status in rows
    ]
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.executemany(statement, normalized)


def resolve_review(program_id, kp_id, user_id) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.film_match_review
            SET status = 'resolved', resolved_kp_id = %s, resolved_by = %s,
                updated_at = SYSDATETIME()
            WHERE oplan_program_id = %s
            """,
            (kp_id, user_id, program_id),
        )


def reject_review(program_id, user_id) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.film_match_review
            SET status = 'rejected', resolved_kp_id = NULL, resolved_by = %s,
                updated_at = SYSDATETIME()
            WHERE oplan_program_id = %s
            """,
            (user_id, program_id),
        )


def revert_review(program_id) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.film_match_review
            SET status = 'pending', resolved_kp_id = NULL, resolved_by = NULL,
                updated_at = SYSDATETIME()
            WHERE oplan_program_id = %s
            """,
            (program_id,),
        )


def fetch_review_item(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            SELECT id, oplan_program_id, bucket, status, resolved_kp_id,
                   run_id, candidates_json
            FROM dbo.film_match_review
            WHERE oplan_program_id = %s
            """,
            (program_id,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    columns = ('id', 'oplan_program_id', 'bucket', 'status', 'resolved_kp_id',
               'run_id', 'candidates_json')
    return dict(zip(columns, row))


# --- Разбор очереди (фильтры) ----------------------------------------------

_FILM_TYPE_SQL = 'p.[program_type_id] IN (5, 6, 10, 11)'
_SERIES_TYPE_SQL = 'p.[program_type_id] IN (4, 12, 16)'

# Поднимаемся по parent_id до корня дерева program. Корень — строка с
# parent_id IS NULL; для материалов это всегда папка канала (или папка
# верхнего уровня, которой нет в constants.CHANNELS → «Без категории»).
#
# ВАЖНО: не добавлять сюда GROUP BY. mssql-django при наличии подстроки
# 'GROUP BY' переписывает запрос и добавляет перед ним DECLARE без ';',
# из-за чего SQL Server отвергает WITH (ошибка 319). Корень выбираем через
# ROW_NUMBER(), а перед WITH оставляем ';' как защиту.
_CHANNEL_CTE = f"""
;WITH ancestor AS (
    SELECT r.[oplan_program_id] AS start_id,
           p.[program_id]       AS node_id,
           p.[parent_id],
           0                    AS depth
    FROM dbo.[film_match_review] AS r
    JOIN [{OPLAN_DB}].[dbo].[program] AS p
      ON p.[program_id] = r.[oplan_program_id]
    UNION ALL
    SELECT a.[start_id], p.[program_id], p.[parent_id], a.[depth] + 1
    FROM ancestor AS a
    JOIN [{OPLAN_DB}].[dbo].[program] AS p
      ON p.[program_id] = a.[parent_id]
    WHERE a.[depth] < 20
),
channel_root AS (
    SELECT roots.[start_id], roots.[node_id] AS [root_id]
    FROM (
        SELECT [start_id], [node_id],
               ROW_NUMBER() OVER (
                   PARTITION BY [start_id]
                   ORDER BY [node_id] DESC
               ) AS [rn]
        FROM ancestor
        WHERE [parent_id] IS NULL OR [parent_id] = 0
    ) AS roots
    WHERE roots.[rn] = 1
)
"""

_LOCK_EDITOR_NAME_SQL = (
    "COALESCE("
    "NULLIF(LTRIM(RTRIM(ed.[full_name])), ''), "
    "NULLIF(LTRIM(RTRIM("
    "ISNULL(au.[first_name], '') + ' ' + ISNULL(au.[last_name], '')"
    ")), ''), "
    "au.[username])"
)

_QUEUE_FROM = f"""
FROM dbo.[film_match_review] AS r
JOIN [{OPLAN_DB}].[dbo].[program] AS p
  ON p.[program_id] = r.[oplan_program_id]
LEFT JOIN channel_root AS ch
  ON ch.[start_id] = r.[oplan_program_id]
LEFT JOIN dbo.[film_review_lock] AS lk
  ON lk.[program_id] = r.[oplan_program_id]
 AND lk.[expires_at] > SYSDATETIME()
LEFT JOIN dbo.[editors_list] AS ed
  ON ed.[planner_editor_id] = lk.[editor_id]
LEFT JOIN dbo.[auth_user] AS au
  ON au.[id] = lk.[editor_id]
"""

_QUEUE_OPTIONS = 'OPTION (MAXRECURSION 32)'

_QUEUE_COUNT_FROM = f"""
FROM dbo.[film_match_review] AS r
JOIN [{OPLAN_DB}].[dbo].[program] AS p
  ON p.[program_id] = r.[oplan_program_id]
LEFT JOIN channel_root AS ch
  ON ch.[start_id] = r.[oplan_program_id]
"""


def _review_queue_filter(status='pending', bucket=None, kind=None,
                         parent_id=None, name=None, channel=None):
    """WHERE-условия очереди разбора, общие для выборки и счётчика."""
    conditions = ['p.[deleted] = 0', 'p.[DeletedIncludeParent] = 0']
    params = []
    if status:
        conditions.append('r.[status] = %s')
        params.append(status)
    if bucket:
        conditions.append('r.[bucket] = %s')
        params.append(bucket)
    if kind == 'film':
        conditions.append(_FILM_TYPE_SQL)
    elif kind == 'series':
        conditions.append(_SERIES_TYPE_SQL)
    if parent_id is not None:
        conditions.append('p.[parent_id] = %s')
        params.append(parent_id)
    if name:
        conditions.append('p.[name] LIKE %s')
        params.append(f'%{name}%')
    if channel == 'none':
        conditions.append(
            f'(ch.[root_id] IS NULL OR ch.[root_id] NOT IN '
            f'({_int_list(constants.CHANNEL_IDS)}))'
        )
    elif channel:
        conditions.append('ch.[root_id] = %s')
        params.append(int(channel))
    return conditions, params


def fetch_review_queue(status='pending', bucket=None, kind=None,
                       parent_id=None, name=None, channel=None,
                       limit=500, offset=0) -> list:
    conditions, params = _review_queue_filter(
        status=status, bucket=bucket, kind=kind, parent_id=parent_id,
        name=name, channel=channel,
    )
    query = f"""
    {_CHANNEL_CTE}
    SELECT r.[oplan_program_id], r.[bucket], r.[status], r.[resolved_kp_id],
           p.[name], p.[orig_name], p.[program_type_id], p.[program_kind],
           p.[production_year], p.[production_country], p.[parent_id],
           ch.[root_id] AS [channel_id],
           lk.[editor_id] AS [locked_by],
           {_LOCK_EDITOR_NAME_SQL} AS [locked_by_name]
    {_QUEUE_FROM}
    WHERE {' AND '.join(conditions)}
    ORDER BY CASE r.[bucket]
                 WHEN 'band_070_085' THEN 0
                 WHEN 'ambiguous' THEN 1
                 ELSE 2 END,
             p.[name], r.[oplan_program_id]
    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    {_QUEUE_OPTIONS}
    """
    params.extend([offset, limit])
    columns = ('oplan_program_id', 'bucket', 'status', 'resolved_kp_id',
               'name', 'orig_name', 'program_type_id', 'program_kind',
               'production_year', 'production_country', 'parent_id',
               'channel_id', 'locked_by', 'locked_by_name')
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(query, params)
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def count_review_queue(status='pending', bucket=None, kind=None,
                       parent_id=None, name=None, channel=None) -> int:
    """Полное число задач по тем же фильтрам, без ограничения страницей."""
    conditions, params = _review_queue_filter(
        status=status, bucket=bucket, kind=kind, parent_id=parent_id,
        name=name, channel=channel,
    )
    query = f"""
    {_CHANNEL_CTE}
    SELECT COUNT(*)
    {_QUEUE_COUNT_FROM}
    WHERE {' AND '.join(conditions)}
    {_QUEUE_OPTIONS}
    """
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(query, params)
        return int(cursor.fetchone()[0])


# --- Аренда карточки при ручном разборе -------------------------------------

def _normalize_editor_name(value) -> str:
    return ' '.join(str(value).split()) if value else ''


def get_review_lock(program_id):
    """Активная аренда карточки или None (просроченные считаются свободными)."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT lk.[editor_id], lk.[locked_at], lk.[expires_at],
                   {_LOCK_EDITOR_NAME_SQL}
            FROM dbo.[film_review_lock] AS lk
            LEFT JOIN dbo.[editors_list] AS ed
              ON ed.[planner_editor_id] = lk.[editor_id]
            LEFT JOIN dbo.[auth_user] AS au
              ON au.[id] = lk.[editor_id]
            WHERE lk.[program_id] = %s
              AND lk.[expires_at] > SYSDATETIME()
            """,
            (program_id,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    return {
        'program_id': program_id,
        'editor_id': row[0],
        'locked_at': row[1],
        'expires_at': row[2],
        'editor_name': _normalize_editor_name(row[3]) or 'Неизвестный редактор',
    }


def claim_review_lock(program_id, user_id, force=False) -> dict:
    """Захватывает/продлевает аренду карточки.

    force=True (только для главного редактора) забирает карточку у другого
    редактора. Возвращает {'status': 'success'|'locked'|'error', ...}.
    """
    ttl = constants.LOCK_TTL_MINUTES
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            'DELETE FROM dbo.[film_review_lock] WHERE [expires_at] <= SYSDATETIME()'
        )

    acquired = False
    try:
        with transaction.atomic(using=PLANNER_DB):
            with connections[PLANNER_DB].cursor() as cursor:
                if force:
                    cursor.execute(
                        'DELETE FROM dbo.[film_review_lock] WHERE [program_id] = %s',
                        (program_id,),
                    )
                    cursor.execute(
                        """
                        INSERT INTO dbo.[film_review_lock]
                            ([program_id], [editor_id], [expires_at])
                        VALUES (%s, %s, DATEADD(MINUTE, %s, SYSDATETIME()))
                        """,
                        (program_id, user_id, ttl),
                    )
                    acquired = True
                else:
                    cursor.execute(
                        """
                        UPDATE dbo.[film_review_lock]
                        SET [editor_id] = %s,
                            [locked_at] = SYSDATETIME(),
                            [expires_at] = DATEADD(MINUTE, %s, SYSDATETIME())
                        WHERE [program_id] = %s
                          AND ([editor_id] = %s OR [expires_at] <= SYSDATETIME())
                        """,
                        (user_id, ttl, program_id, user_id),
                    )
                    acquired = cursor.rowcount > 0

                    if not acquired:
                        # UPDLOCK/HOLDLOCK не даёт двум редакторам одновременно
                        # вставить аренду для одной и той же карточки.
                        cursor.execute(
                            """
                            SELECT [editor_id]
                            FROM dbo.[film_review_lock] WITH (UPDLOCK, HOLDLOCK)
                            WHERE [program_id] = %s
                            """,
                            (program_id,),
                        )
                        if not cursor.fetchall():
                            cursor.execute(
                                """
                                INSERT INTO dbo.[film_review_lock]
                                    ([program_id], [editor_id], [expires_at])
                                VALUES (%s, %s, DATEADD(MINUTE, %s, SYSDATETIME()))
                                """,
                                (program_id, user_id, ttl),
                            )
                            acquired = True
    except IntegrityError:
        # Кто-то успел вставить аренду между UPDATE и INSERT.
        acquired = False

    lock = get_review_lock(program_id)
    if acquired and lock and lock['editor_id'] == user_id:
        return {
            'status': 'success',
            'expires_at': lock['expires_at'].isoformat(),
            'ttl_seconds': ttl * 60,
        }
    if lock:
        return {
            'status': 'locked',
            'program_id': program_id,
            'editor_id': lock['editor_id'],
            'editor_name': lock['editor_name'],
        }
    return {'status': 'error', 'message': 'Не удалось заблокировать карточку'}


def release_review_lock(program_id, user_id=None) -> None:
    sql = 'DELETE FROM dbo.[film_review_lock] WHERE [program_id] = %s'
    params = [program_id]
    if user_id is not None:
        sql += ' AND [editor_id] = %s'
        params.append(user_id)
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(sql, params)


def is_locked_by_other(program_id, user_id) -> bool:
    lock = get_review_lock(program_id)
    return bool(lock and lock['editor_id'] != user_id)


def review_stats() -> list:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            SELECT status, bucket, COUNT(*) AS cnt
            FROM dbo.film_match_review
            GROUP BY status, bucket
            """
        )
        return [{'status': row[0], 'bucket': row[1], 'count': row[2]}
                for row in cursor.fetchall()]


# --- Применение/отмена ручного сопоставления -------------------------------

_PROPAGATE_SUBQUERY = (
    f"SELECT [program_id] FROM [{OPLAN_DB}].[dbo].[program] WHERE [parent_id] = %s"
)


def apply_manual_match(program_id, kp_id) -> None:
    """Проставляет kinopoisk_id родителю (kind=4/0) и его сериям (kind=3)."""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            MERGE dbo.film_material_index AS target
            USING (SELECT %s AS oplan_program_id, %s AS kinopoisk_id) AS source
            ON target.oplan_program_id = source.oplan_program_id
            WHEN MATCHED THEN UPDATE SET
                target.kinopoisk_id = source.kinopoisk_id,
                target.match_source = 'manual',
                target.refreshed_at = SYSDATETIME()
            WHEN NOT MATCHED THEN INSERT
                (oplan_program_id, kinopoisk_id, has_file, duration_frames, match_source)
                VALUES (source.oplan_program_id, source.kinopoisk_id, 0, NULL, 'manual');
            """,
            (program_id, kp_id),
        )
        cursor.execute(
            f"""
            UPDATE dbo.film_material_index
            SET kinopoisk_id = %s, match_source = 'manual', refreshed_at = SYSDATETIME()
            WHERE oplan_program_id IN ({_PROPAGATE_SUBQUERY})
            """,
            (kp_id, program_id),
        )


def clear_manual_match(program_id) -> None:
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.film_material_index
            SET kinopoisk_id = NULL, match_source = NULL, refreshed_at = SYSDATETIME()
            WHERE oplan_program_id = %s
            """,
            (program_id,),
        )
        cursor.execute(
            f"""
            UPDATE dbo.film_material_index
            SET kinopoisk_id = NULL, match_source = NULL, refreshed_at = SYSDATETIME()
            WHERE oplan_program_id IN ({_PROPAGATE_SUBQUERY})
            """,
            (program_id,),
        )
