from django.core.management.base import BaseCommand

from tools.posters import delete_poster


class Command(BaseCommand):
    help = 'Delete cached posters for one or more Oplan program ids'

    def add_arguments(self, parser):
        parser.add_argument('program_ids', nargs='+', type=int)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        errors = 0

        for program_id in options['program_ids']:
            self.stdout.write(f'program_id={program_id}')
            result = delete_poster(program_id, dry_run=dry_run)
            for name, status in result.items():
                if status.startswith('error'):
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'  [{status}] {name}'))
                elif status == 'missing':
                    self.stdout.write(f'  [missing] {name}')
                elif status == 'would-delete':
                    self.stdout.write(self.style.WARNING(f'  [would-delete] {name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  [deleted] {name}'))

        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {errors}'))
