import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from messenger_static.models import Message
from main.models import AttachedFiles


class Command(BaseCommand):
    help = 'Migrate all local media files to S3/MinIO storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually copying',
        )
        parser.add_argument(
            '--posters',
            action='store_true',
            help='Also migrate poster files from local disk',
        )
        parser.add_argument(
            '--waveforms',
            action='store_true',
            help='Also migrate waveform files from local disk',
        )

    def _listdir_safe(self, dir_path, extension):
        try:
            return [f for f in os.listdir(dir_path) if f.endswith(extension)]
        except PermissionError:
            self.stdout.write(self.style.ERROR(
                f'Permission denied: {dir_path}\n'
                f'  Run on host: chmod o+rX "{dir_path}"'
            ))
            return []
        except FileNotFoundError:
            return []

    def _should_migrate(self, s3_key):
        try:
            return not default_storage.exists(s3_key)
        except Exception:
            return True

    def _copy_file(self, local_path, s3_key, dry_run):
        if not os.path.isfile(local_path):
            return 'no_local'
        if not self._should_migrate(s3_key):
            return 'exists'
        if not dry_run:
            with open(local_path, 'rb') as f:
                default_storage.save(s3_key, ContentFile(f.read()))
        return 'ok'

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        total = 0
        migrated = 0
        skipped_exists = 0
        skipped_no_local = 0
        errors = 0

        header = '=' * 60
        self.stdout.write(self.style.WARNING(header))
        self.stdout.write(self.style.WARNING('S3 Migration Tool'))
        self.stdout.write(self.style.WARNING(header))

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n*** DRY RUN MODE — nothing will be copied ***\n'))

        if not getattr(settings, 'USE_S3_STORAGE', False):
            self.stdout.write(self.style.WARNING(
                'USE_S3_STORAGE is not enabled. Migration will work, but double-check your .env.'
            ))

        # Chat files (Message)
        self.stdout.write('\n--- Chat files (Message) ---')
        messages = Message.objects.exclude(file_path='').exclude(file_path__isnull=True)
        self.stdout.write(f'Found {messages.count()} messages with files')
        for msg in messages:
            total += 1
            local_path = os.path.join(settings.MEDIA_ROOT, msg.file_path.name)
            try:
                result = self._copy_file(local_path, msg.file_path.name, dry_run)
                if result == 'ok':
                    migrated += 1
                    self.stdout.write(f'  [OK] {msg.file_path.name}')
                elif result == 'exists':
                    skipped_exists += 1
                    self.stdout.write(f'  [SKIP] already in S3: {msg.file_path.name}')
                elif result == 'no_local':
                    skipped_no_local += 1
                    self.stdout.write(self.style.WARNING(f'  [SKIP] local file not found: {local_path}'))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  [ERR] {msg.file_path.name}: {e}'))

        # Attached files (AttachedFiles)
        self.stdout.write('\n--- Attached program files (AttachedFiles) ---')
        attached = AttachedFiles.objects.exclude(file_path='').exclude(file_path__isnull=True)
        self.stdout.write(f'Found {attached.count()} attached files')
        for af in attached:
            total += 1
            local_path = os.path.join(settings.MEDIA_ROOT, af.file_path.name)
            try:
                result = self._copy_file(local_path, af.file_path.name, dry_run)
                if result == 'ok':
                    migrated += 1
                    self.stdout.write(f'  [OK] {af.file_path.name}')
                elif result == 'exists':
                    skipped_exists += 1
                    self.stdout.write(f'  [SKIP] already in S3: {af.file_path.name}')
                elif result == 'no_local':
                    skipped_no_local += 1
                    self.stdout.write(self.style.WARNING(f'  [SKIP] local file not found: {local_path}'))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  [ERR] {af.file_path.name}: {e}'))

        # Posters
        if options['posters']:
            self.stdout.write('\n--- Poster files ---')
            posters_dir = os.path.join(settings.MEDIA_ROOT, 'posters')
            poster_files = self._listdir_safe(posters_dir, '.jpg')
            if poster_files:
                self.stdout.write(f'Found {len(poster_files)} poster files')
                for pf in poster_files:
                    total += 1
                    local_path = os.path.join(posters_dir, pf)
                    s3_key = f'posters/{pf}'
                    try:
                        result = self._copy_file(local_path, s3_key, dry_run)
                        if result == 'ok':
                            migrated += 1
                            self.stdout.write(f'  [OK] {s3_key}')
                        elif result == 'exists':
                            skipped_exists += 1
                            self.stdout.write(f'  [SKIP] already in S3: {s3_key}')
                        elif result == 'no_local':
                            skipped_no_local += 1
                            self.stdout.write(self.style.WARNING(f'  [SKIP] local file not found: {local_path}'))
                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'  [ERR] {s3_key}: {e}'))
            else:
                self.stdout.write(self.style.WARNING('  No posters/ directory found'))

        # Waveforms
        if options['waveforms']:
            self.stdout.write('\n--- Waveform files ---')
            waveforms_dir = settings.MEDIA_WAVEFORMS
            waveform_files = self._listdir_safe(waveforms_dir, '.png')
            if waveform_files:
                self.stdout.write(f'Found {len(waveform_files)} waveform files')
                for wf in waveform_files:
                    total += 1
                    local_path = os.path.join(waveforms_dir, wf)
                    s3_key = f'waveforms/{wf}'
                    try:
                        result = self._copy_file(local_path, s3_key, dry_run)
                        if result == 'ok':
                            migrated += 1
                            self.stdout.write(f'  [OK] {s3_key}')
                        elif result == 'exists':
                            skipped_exists += 1
                            self.stdout.write(f'  [SKIP] already in S3: {s3_key}')
                        elif result == 'no_local':
                            skipped_no_local += 1
                            self.stdout.write(self.style.WARNING(f'  [SKIP] local file not found: {local_path}'))
                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'  [ERR] {s3_key}: {e}'))
            else:
                self.stdout.write(self.style.WARNING('  No waveforms directory found'))

        # Summary
        self.stdout.write(self.style.WARNING('\n' + header))
        self.stdout.write(f'Total:      {total}')
        self.stdout.write(self.style.SUCCESS(f'Migrated:   {migrated}'))
        self.stdout.write(f'Skipped (already in S3):   {skipped_exists}')
        self.stdout.write(f'Skipped (local not found): {skipped_no_local}')
        self.stdout.write(self.style.ERROR(f'Errors:     {errors}'))
        self.stdout.write(self.style.WARNING(header))
