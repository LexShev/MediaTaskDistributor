"""Clear planner tables used by the film_index matching workflow."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from planner.settings import PLANNER_DB


TABLES = (
    'film_match_staging',
    'film_match_review',
    'film_review_lock',
    'film_match_run',
    'film_material_index',
)


class Command(BaseCommand):
    help = 'Очищает таблицы film_index в Planner MSSQL перед повторным сопоставлением'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Подтвердить очистку таблиц',
        )

    def handle(self, *args, **options):
        if not options['yes']:
            raise CommandError('Очистка не подтверждена. Добавьте --yes.')

        with connections[PLANNER_DB].cursor() as cursor:
            for table in TABLES:
                cursor.execute(
                    f"IF OBJECT_ID('dbo.{table}', 'U') IS NOT NULL "
                    f"EXEC('TRUNCATE TABLE dbo.{table}')"
                )
                self.stdout.write(f'Очищена таблица dbo.{table}')

        self.stdout.write(self.style.SUCCESS('Таблицы film_index очищены'))
