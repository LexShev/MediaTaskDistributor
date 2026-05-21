# planner/file_manager/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class FileCopyTask(models.Model):
    """Модель для отслеживания задач копирования файлов"""

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('copying', 'Копирование'),
        ('verifying', 'Проверка'),
        ('completed', 'Завершено'),
        ('error', 'Ошибка'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('normal', 'Обычный'),
        ('high', 'Высокий'),
    ]

    # Основные поля
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='file_copy_tasks',
        verbose_name='Владелец'
    )
    celery_task_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Celery Task ID'
    )

    # Информация о файле
    file_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='ID файла в системе'
    )
    file_path = models.TextField(verbose_name='Путь к файлу')
    file_name = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Имя файла'
    )
    destination_path = models.TextField(verbose_name='Путь назначения')

    # Статус и прогресс
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    progress = models.FloatField(
        default=0.0,
        verbose_name='Прогресс (%)'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='Приоритет'
    )

    # Статистика копирования
    file_size_gb = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Размер файла (GB)'
    )
    speed_mbps = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Скорость (MB/s)'
    )
    transferred_gb = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Передано (GB)'
    )

    # Хэши для верификации
    source_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Хэш источника'
    )
    dest_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Хэш копии'
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Начало копирования'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Завершено'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    # Дополнительно
    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name='Комментарий'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ошибка'
    )
    retry_count = models.IntegerField(
        default=0,
        verbose_name='Количество попыток'
    )

    class Meta:
        verbose_name = 'Задача копирования'
        verbose_name_plural = 'Задачи копирования'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['celery_task_id']),
        ]

    def __str__(self):
        return f"Copy: {self.file_name} -> {self.destination_path} [{self.status}]"

    @property
    def duration(self):
        """Вычисляет длительность копирования"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def can_retry(self):
        """Можно ли повторить задачу"""
        return self.status in ['completed', 'error']

    @property
    def is_active(self):
        """Активна ли задача"""
        return self.status in ['pending', 'copying', 'verifying']