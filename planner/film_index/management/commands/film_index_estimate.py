"""Оценка объёма ручной проверки: сопоставление выборки материалов Oplan3
с каталогом Кинопоиска и отчёт по бакетам.

Команда НИЧЕГО не пишет в БД (только читает Oplan3/Mongo) и печатает
распределение: сколько материалов сопоставляется уверенно (auto_high),
сколько попадает в диапазон 0.70-0.85, сколько неоднозначно и сколько не
найдено вовсе.
"""

import random
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError

from film_index import constants, matching
from film_index.kinopoisk_source import load_catalog
from film_index.oplan_source import fetch_match_targets

KIND_LABELS = {
    0: 'фильм',
    1: 'папка-коллекция',
    3: 'серия',
    4: 'родитель сезона',
    6: 'служебное',
}


class Command(BaseCommand):
    help = 'Оценка доли материалов, уходящих на ручную проверку (без записи в БД)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample', type=int, default=constants.DEFAULT_SAMPLE,
            help=f'Размер выборки (по умолчанию {constants.DEFAULT_SAMPLE})',
        )
        parser.add_argument('--seed', type=int, default=42, help='Seed выборки')
        parser.add_argument(
            '--examples', type=int, default=8,
            help='Сколько примеров показать на каждый бакет',
        )

    def handle(self, *args, **options):
        sample_size = options['sample']
        seed = options['seed']
        examples_limit = options['examples']

        self.stdout.write('Загрузка материалов Oplan3...')
        targets = fetch_match_targets()
        total_targets = len(targets)
        self.stdout.write(f'  к сопоставлению (фильмы+родители): {total_targets}')

        if not targets:
            raise CommandError('Не найдено ни одного материала для сопоставления')

        if total_targets <= sample_size:
            sample = targets
        else:
            sample = random.Random(seed).sample(targets, sample_size)

        self.stdout.write('Загрузка каталога Кинопоиска (Mongo)...')
        try:
            catalog = load_catalog()
        except Exception as error:  # noqa: BLE001 - хотим внятный вывод
            raise CommandError(f'Не удалось загрузить каталог Кинопоиска: {error}')

        self.stdout.write(f'  документов в каталоге: {catalog.size}')
        self.stdout.write('Сопоставление...')

        counts = Counter()
        by_type = defaultdict(Counter)
        by_kind = defaultdict(Counter)
        unresolved_by_parent = Counter()
        examples = {bucket: [] for bucket in constants.BUCKETS}

        for material in sample:
            outcome = matching.match_material(material, catalog)
            bucket = outcome.bucket
            counts[bucket] += 1
            by_type[material.get('program_type_id')][bucket] += 1
            by_kind[material.get('program_kind')][bucket] += 1
            if bucket != constants.BUCKET_AUTO_HIGH:
                unresolved_by_parent[material.get('parent_id')] += 1
            if len(examples[bucket]) < examples_limit:
                examples[bucket].append((material, outcome))

        self._print_buckets(counts, len(sample), total_targets)
        self._print_by_type(by_type)
        self._print_by_kind(by_kind)
        self._print_unresolved_by_parent(unresolved_by_parent)
        self._print_examples(examples)

    def _print_buckets(self, counts, sample_count, total_targets):
        self.stdout.write('')
        self.stdout.write('=== Бакеты (выборка / экстраполяция на всю БД) ===')
        header = f'{"bucket":<14}{"кол-во":>10}{"доля":>10}{"~на всю БД":>14}'
        self.stdout.write(header)
        for bucket in constants.BUCKETS:
            count = counts.get(bucket, 0)
            share = count / sample_count if sample_count else 0
            projected = round(share * total_targets)
            self.stdout.write(
                f'{bucket:<14}{count:>10}{share * 100:>9.1f}%{projected:>14}'
            )

    def _print_by_type(self, by_type):
        self.stdout.write('')
        self.stdout.write('=== Разбивка по program_type_id ===')
        header = (
            f'{"type":>6}{"всего":>9}{"auto_high":>11}'
            f'{"band":>8}{"ambig":>8}{"unmatched":>11}'
        )
        self.stdout.write(header)
        for type_id in sorted(by_type, key=lambda value: (value is None, value)):
            row = by_type[type_id]
            total = sum(row.values())
            self.stdout.write(
                f'{str(type_id):>6}{total:>9}'
                f'{row.get(constants.BUCKET_AUTO_HIGH, 0):>11}'
                f'{row.get(constants.BUCKET_BAND, 0):>8}'
                f'{row.get(constants.BUCKET_AMBIGUOUS, 0):>8}'
                f'{row.get(constants.BUCKET_UNMATCHED, 0):>11}'
            )

    def _print_by_kind(self, by_kind):
        self.stdout.write('')
        self.stdout.write('=== Разбивка по program_kind ===')
        header = (
            f'{"kind":>6}{"":<16}{"всего":>9}{"auto_high":>11}'
            f'{"band":>8}{"ambig":>8}{"unmatched":>11}'
        )
        self.stdout.write(header)
        for kind in sorted(by_kind, key=lambda value: (value is None, value)):
            row = by_kind[kind]
            total = sum(row.values())
            self.stdout.write(
                f'{str(kind):>6}{KIND_LABELS.get(kind, ""):<16}{total:>9}'
                f'{row.get(constants.BUCKET_AUTO_HIGH, 0):>11}'
                f'{row.get(constants.BUCKET_BAND, 0):>8}'
                f'{row.get(constants.BUCKET_AMBIGUOUS, 0):>8}'
                f'{row.get(constants.BUCKET_UNMATCHED, 0):>11}'
            )

    def _print_unresolved_by_parent(self, unresolved_by_parent, limit=10):
        if not unresolved_by_parent:
            return
        self.stdout.write('')
        self.stdout.write('=== Топ parent_id по неразобранным (band/ambig/unmatched) ===')
        for parent_id, count in unresolved_by_parent.most_common(limit):
            self.stdout.write(f'  parent_id={parent_id}: {count}')

    def _print_examples(self, examples):
        titles = {
            constants.BUCKET_AUTO_HIGH: 'auto_high',
            constants.BUCKET_BAND: 'band_070_085',
            constants.BUCKET_AMBIGUOUS: 'ambiguous',
            constants.BUCKET_UNMATCHED: 'unmatched',
        }
        for bucket in constants.BUCKETS:
            rows = examples.get(bucket) or []
            if not rows:
                continue
            self.stdout.write('')
            self.stdout.write(f'=== Примеры [{titles[bucket]}] ===')
            for material, outcome in rows:
                self.stdout.write(
                    f'\nOplan [{material.get("program_id")}] '
                    f'"{material.get("name")}" '
                    f'({material.get("production_year")}, '
                    f'{material.get("production_country")}) '
                    f'реж: {material.get("director")}'
                )
                for candidate in outcome.candidates[:3]:
                    entry = candidate.entry
                    flag = 'director+' if candidate.director_match else ''
                    self.stdout.write(
                        f'    -> [{entry["kp_id"]}] "{entry["title"]}" '
                        f'({entry["year"]}) score={candidate.score:.3f} '
                        f't={candidate.title_score:.2f} y={candidate.year_score:.0f} '
                        f'c={candidate.country_score:.2f} '
                        f'd={candidate.director_score:.2f} {flag}'
                    )
