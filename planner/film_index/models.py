"""ORM-модели модуля film_index.

Таблицы модуля уже созданы (см. ``sql_scripts/film_index.sql`` и
``film_index/schema.py``). Все модели помечены ``managed = False``, поэтому
Django их не создаёт и не изменяет — они используются только для доступа к
существующим таблицам через подключение по умолчанию (БД ``planner``).

Типы колонок:
* ``INT`` -> ``IntegerField``;
* ``BIGINT IDENTITY`` -> ``BigAutoField``;
* ``UNIQUEIDENTIFIER`` -> ``UUIDField``;
* ``BIT`` -> ``BooleanField``;
* ``FLOAT`` -> ``FloatField``;
* ``DATETIME2`` -> ``DateTimeField``;
* ``VARCHAR(n)`` -> ``CharField(max_length=n)``;
* ``NVARCHAR(MAX)`` -> ``TextField``.
"""

from django.db import models


class FilmMaterialIndex(models.Model):
    """Рантайм-проекция: привязка oplan_program_id <-> kinopoisk_id + наличие файла."""

    oplan_program_id = models.IntegerField(primary_key=True)
    kinopoisk_id = models.IntegerField(null=True, blank=True)
    has_file = models.BooleanField(default=False)
    duration_frames = models.IntegerField(null=True, blank=True)
    refreshed_at = models.DateTimeField(auto_now=True)
    match_source = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'film_material_index'
        verbose_name = 'film material index'
        verbose_name_plural = 'film material index'

    def __str__(self):
        return f'{self.oplan_program_id} -> {self.kinopoisk_id}'


class FilmMatchStaging(models.Model):
    """Аудит сопоставления: по строке на материал за прогон."""

    id = models.BigAutoField(primary_key=True)
    run_id = models.UUIDField()
    oplan_program_id = models.IntegerField()
    candidate_kp_id = models.IntegerField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    title_score = models.FloatField(null=True, blank=True)
    year_score = models.FloatField(null=True, blank=True)
    country_score = models.FloatField(null=True, blank=True)
    bucket = models.CharField(max_length=20)
    reason = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'film_match_staging'
        verbose_name = 'film match staging'
        verbose_name_plural = 'film match staging'

    def __str__(self):
        return f'{self.oplan_program_id} [{self.bucket}]'


class FilmMatchReview(models.Model):
    """Очередь ручного разбора сопоставления."""

    id = models.BigAutoField(primary_key=True)
    oplan_program_id = models.IntegerField()
    run_id = models.UUIDField(null=True, blank=True)
    candidates_json = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    resolved_kp_id = models.IntegerField(null=True, blank=True)
    resolved_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    bucket = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'film_match_review'
        verbose_name = 'film match review'
        verbose_name_plural = 'film match review'

    def __str__(self):
        return f'{self.oplan_program_id} [{self.status}]'


class FilmMatchRun(models.Model):
    """Метаданные прогона сопоставления."""

    id = models.UUIDField(primary_key=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    mode = models.CharField(max_length=20, null=True, blank=True)
    sample_size = models.IntegerField(null=True, blank=True)
    total_targets = models.IntegerField(null=True, blank=True)
    auto_high = models.IntegerField(null=True, blank=True)
    band = models.IntegerField(null=True, blank=True)
    ambiguous = models.IntegerField(null=True, blank=True)
    unmatched = models.IntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'film_match_run'
        verbose_name = 'film match run'
        verbose_name_plural = 'film match run'

    def __str__(self):
        return f'run {self.id} [{self.mode}]'
