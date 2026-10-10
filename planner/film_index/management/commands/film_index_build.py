"""Полный прогон сопоставления и наполнение film_material_index.

По умолчанию работает в режиме dry-run (ничего не пишет). С флагом --apply:

* пишет результаты сопоставления в film_match_staging;
* спорные/ненайденные материалы кладёт в film_match_review (pending),
  сохраняя ручные решения (resolved/rejected) и не возвращая их в очередь;
* заполняет film_material_index (kinopoisk_id для auto_high, has_file и
  duration_frames для всех материалов; серии наследуют kinopoisk_id родителя).

Ручные сопоставления (match_source='manual') не перетираются.
"""

import random
from collections import Counter
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError

from film_index import constants, matching, oplan_source, repository, schema
from film_index.kinopoisk_source import load_catalog
from film_index.oplan_source import fetch_materials, is_match_target


class Command(BaseCommand):
    help = 'Сопоставить материалы Oplan3 с Кинопоиском и наполнить film_material_index'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Записать результат в БД (иначе dry-run)')
        parser.add_argument('--sample', type=int, default=0, help='Ограничить число сопоставляемых материалов (0 = все)')
        parser.add_argument('--seed', type=int, default=42, help='Seed выборки')
        parser.add_argument('--no-staging', action='store_true', help='Не писать film_match_staging')
        parser.add_argument('--no-review', action='store_true', help='Не писать/не обновлять film_match_review')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        sample_size = options['sample']
        seed = options['seed']

        manual_matches = {}
        excluded_review_ids = set()
        if apply_changes:
            schema.ensure_schema()
        try:
            manual_matches = repository.load_manual_matches()
            excluded_review_ids = repository.load_excluded_review_ids()
        except Exception as error:  # noqa: BLE001 - таблиц может ещё не быть
            self.stdout.write(self.style.WARNING(f'Не удалось прочитать ручные решения: {error}'))

        self.stdout.write('Загрузка материалов Oplan3...')
        materials = fetch_materials()
        targets = [material for material in materials if is_match_target(material)]
        if not targets:
            raise CommandError('Не найдено ни одного материала для сопоставления')

        pending_targets = [m for m in targets if m['program_id'] not in manual_matches]
        match_targets = pending_targets
        if sample_size and sample_size < len(pending_targets):
            match_targets = random.Random(seed).sample(pending_targets, sample_size)

        self.stdout.write(f'  всего строк-материалов: {len(materials)}')
        self.stdout.write(f'  к сопоставлению: {len(targets)} (вручную уже решено: {len(manual_matches)})')
        self.stdout.write(f'  в этом прогоне: {len(match_targets)}')

        self.stdout.write('Загрузка каталога Кинопоиска (Mongo)...')
        try:
            catalog = load_catalog()
        except Exception as error:  # noqa: BLE001
            raise CommandError(f'Не удалось загрузить каталог Кинопоиска: {error}')
        self.stdout.write(f'  документов в каталоге: {catalog.size}')

        self.stdout.write('Сопоставление...')
        counts = Counter()
        kp_by_program = dict(manual_matches)
        source_by_program = {pid: 'manual' for pid in manual_matches}
        staging_rows = []
        review_rows = []
        run_id = uuid4()

        for material in match_targets:
            outcome = matching.match_material(material, catalog)
            counts[outcome.bucket] += 1
            program_id = material['program_id']
            if outcome.bucket == constants.BUCKET_AUTO_HIGH and outcome.best is not None:
                kp_by_program[program_id] = outcome.best.entry['kp_id']
                source_by_program[program_id] = 'auto'

            if not options['no_staging']:
                best = outcome.best
                staging_rows.append((
                    run_id, program_id,
                    best.entry['kp_id'] if best else None,
                    best.score if best else None,
                    best.title_score if best else None,
                    best.year_score if best else None,
                    best.country_score if best else None,
                    outcome.bucket, outcome.reason,
                ))

            if (not options['no_review']
                    and outcome.bucket != constants.BUCKET_AUTO_HIGH
                    and program_id not in excluded_review_ids):
                review_rows.append((
                    program_id, run_id,
                    matching.candidates_to_json(outcome.candidates),
                    outcome.bucket, 'pending',
                ))

        index_rows = self._build_index_rows(materials, kp_by_program, source_by_program)
        matched_index = sum(1 for row in index_rows if row[1] is not None)

        self.stdout.write('')
        self.stdout.write('=== Итог ===')
        for bucket in constants.BUCKETS:
            self.stdout.write(f'  {bucket}: {counts.get(bucket, 0)}')
        self.stdout.write(f'  вручную решено (не пересопоставлялись): {len(manual_matches)}')
        self.stdout.write(f'  строк в film_material_index: {len(index_rows)} (с kinopoisk_id: {matched_index})')
        self.stdout.write(f'  на ручную проверку (pending): {len(review_rows)}')

        if not apply_changes:
            self.stdout.write(self.style.WARNING('DRY-RUN: изменения не записаны (--apply для записи)'))
            return

        repository.create_run(run_id, 'build', len(match_targets), len(targets))
        repository.upsert_index(index_rows)
        if staging_rows:
            repository.insert_staging(staging_rows)
        if not options['no_review']:
            repository.reset_pending_review()
            if review_rows:
                repository.insert_review(review_rows)
        repository.finish_run(run_id, {
            'auto_high': counts.get(constants.BUCKET_AUTO_HIGH, 0),
            'band': counts.get(constants.BUCKET_BAND, 0),
            'ambiguous': counts.get(constants.BUCKET_AMBIGUOUS, 0),
            'unmatched': counts.get(constants.BUCKET_UNMATCHED, 0),
        }, notes=f'index_rows={len(index_rows)}, matched={matched_index}, manual={len(manual_matches)}')
        self.stdout.write(self.style.SUCCESS(f'Готово. run_id={run_id}'))

    def _build_index_rows(self, materials, kp_by_program, source_by_program):
        rows = []
        for material in materials:
            program_id = material['program_id']
            if material.get('program_kind') == constants.EPISODE_KIND:
                parent_id = material.get('parent_id')
                kp_id = kp_by_program.get(parent_id)
                match_source = source_by_program.get(parent_id)
            else:
                kp_id = kp_by_program.get(program_id)
                match_source = source_by_program.get(program_id)
            rows.append((
                program_id,
                kp_id,
                bool(material.get('has_file')),
                oplan_source.duration_frames(material),
                match_source,
            ))
        return rows
