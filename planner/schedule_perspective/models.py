"""Модели модуля перспективных сеток (БД Planner).

Схема описана в `features/schedule-perspective.md`. Таблицы живут в БД Planner
(alias `default` = `planner`); Oplan3 только читаем.

- `PerspectiveDay` — статус и аудит утверждения на конкретный день канала.
- `PerspectiveSlot` — реальная позиция эфира. Ссылается либо на материал
  Oplan3 (`oplan_program_id`), либо на узел отсутствующего материала
  (`no_material_id`).
- `PerspectiveNoMaterial` — иерархия ТОЛЬКО отсутствующих в Oplan материалов
  (каталог → сезон → серия / фильм), в единственном экземпляре на материал.
"""

from django.db import models


class PerspectiveNoMaterial(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        db_column='parent_id', related_name='children',
    )
    # kind по аналогии с Oplan3.program.program_kind: 1 каталог / 4 сезон /
    # 3 серия / 0 фильм.
    kind = models.SmallIntegerField()
    kinopoisk_id = models.IntegerField(null=True, blank=True)
    season_num = models.IntegerField(null=True, blank=True)
    episode_num = models.IntegerField(null=True, blank=True)
    # Появится после синхронизации, когда материал заведут в Oplan3.
    oplan_program_id = models.IntegerField(null=True, blank=True)
    # Снапшот названия: рендер окна не должен зависеть от доступности Mongo.
    title = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perspective_no_material'
        indexes = [
            models.Index(fields=['kinopoisk_id'], name='IX_pnm_kp'),
            models.Index(fields=['parent'], name='IX_pnm_parent'),
        ]

    def __str__(self):
        return f'[{self.kind}] {self.title or self.kinopoisk_id}'


class PerspectiveSlot(models.Model):
    id = models.BigAutoField(primary_key=True)
    schedule_id = models.IntegerField()
    day_date = models.DateField()
    position = models.IntegerField()
    oplan_program_id = models.IntegerField(null=True, blank=True)
    no_material = models.ForeignKey(
        PerspectiveNoMaterial, null=True, blank=True,
        on_delete=models.SET_NULL, db_column='no_material_id',
        related_name='slots',
    )
    duration_frames = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perspective_slot'
        unique_together = (('schedule_id', 'day_date', 'position'),)
        indexes = [
            models.Index(fields=['schedule_id', 'day_date', 'position'], name='IX_ps_day'),
            models.Index(fields=['oplan_program_id'], name='IX_ps_oplan'),
        ]

    def __str__(self):
        return f'{self.schedule_id} {self.day_date} #{self.position}'


class PerspectiveDay(models.Model):
    id = models.BigAutoField(primary_key=True)
    schedule_id = models.IntegerField()
    day_date = models.DateField()
    status = models.CharField(max_length=20, default='draft')
    approved_by = models.IntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    final_by = models.IntegerField(null=True, blank=True)
    final_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perspective_day'
        unique_together = (('schedule_id', 'day_date'),)

    def __str__(self):
        return f'{self.schedule_id} {self.day_date} ({self.status})'
