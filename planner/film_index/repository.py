"""Запись результатов film_index в БД Planner."""

import json

from django.db import connections

from planner.settings import OPLAN_DB, PLANNER_DB


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


def fetch_review_queue(status='pending', bucket=None, kind=None,
                       parent_id=None, name=None, limit=500, offset=0) -> list:
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

    query = f"""
    SELECT r.[oplan_program_id], r.[bucket], r.[status], r.[resolved_kp_id],
           p.[name], p.[orig_name], p.[program_type_id], p.[program_kind],
           p.[production_year], p.[production_country], p.[parent_id]
    FROM dbo.[film_match_review] AS r
    JOIN [{OPLAN_DB}].[dbo].[program] AS p ON p.[program_id] = r.[oplan_program_id]
    WHERE {' AND '.join(conditions)}
    ORDER BY CASE r.[bucket]
                 WHEN 'band_070_085' THEN 0
                 WHEN 'ambiguous' THEN 1
                 ELSE 2 END,
             p.[name], r.[oplan_program_id]
    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """
    params.extend([offset, limit])
    columns = ('oplan_program_id', 'bucket', 'status', 'resolved_kp_id',
               'name', 'orig_name', 'program_type_id', 'program_kind',
               'production_year', 'production_country', 'parent_id')
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(query, params)
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


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
