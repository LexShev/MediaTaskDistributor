"""Запись результатов film_index в БД Planner."""

import json

from django.db import connections

from planner.settings import PLANNER_DB


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


def upsert_index(rows: list) -> None:
    """rows: (oplan_program_id, kinopoisk_id, has_file, duration_frames)."""
    if not rows:
        return
    statement = """
    MERGE dbo.film_material_index AS target
    USING (SELECT %s AS oplan_program_id, %s AS kinopoisk_id,
                  %s AS has_file, %s AS duration_frames) AS source
    ON target.oplan_program_id = source.oplan_program_id
    WHEN MATCHED THEN UPDATE SET
        target.kinopoisk_id = source.kinopoisk_id,
        target.has_file = source.has_file,
        target.duration_frames = source.duration_frames,
        target.refreshed_at = SYSDATETIME()
    WHEN NOT MATCHED THEN INSERT
        (oplan_program_id, kinopoisk_id, has_file, duration_frames)
        VALUES (source.oplan_program_id, source.kinopoisk_id,
                source.has_file, source.duration_frames);
    """
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.executemany(statement, rows)


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
    """rows: (oplan_program_id, run_id, candidates(list), status)."""
    if not rows:
        return
    statement = """
    INSERT INTO dbo.film_match_review
        (oplan_program_id, run_id, candidates_json, status)
    VALUES (%s, %s, %s, %s)
    """
    normalized = [
        (oplan_program_id, str(run_id),
         json.dumps(candidates, ensure_ascii=False), status)
        for oplan_program_id, run_id, candidates, status in rows
    ]
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.executemany(statement, normalized)
