import json
import os.path

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from planner.settings import BASE_DIR


GROUPS = (
    'moderators',
    'preparation_engineers',
    'broadcast_engineers',
    'otk_engineers',
    'editors',
    'video_editors',
    'senior_editor',
    'chief_editor'
)


class Command(BaseCommand):
    help = 'Создаёт пользователей из workers/.users.json и добавляет их в группы.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать действия без создания групп и пользователей',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY-RUN: изменения не применяются.'
            ))

        groups = {}
        for group_name in GROUPS:
            if dry_run:
                group = Group.objects.filter(name=group_name).first()
                groups[group_name] = group
                state = 'существует' if group else 'будет создана'
                self.stdout.write(f'Группа {group_name}: {state}')
            else:
                groups[group_name] = Group.objects.get_or_create(name=group_name)[0]

        with open(os.path.join(BASE_DIR, 'workers/.users.json'), 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        created_count = 0
        for user_data in users_data:
            if User.objects.filter(id=user_data['id']).exists():
                self.stdout.write(
                    f"Пользователь с ID {user_data['id']} уже существует, пропускаем"
                )
                continue

            if User.objects.filter(username=user_data['username']).exists():
                self.stdout.write(
                    f"Пользователь {user_data['username']} уже существует, пропускаем"
                )
                continue

            if dry_run:
                created_count += 1
                self.stdout.write(
                    f"Будет создан пользователь {user_data['username']} "
                    f"с ID {user_data['id']}"
                )
                continue

            try:
                user = User.objects.create_user(
                    id=user_data['id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    password=user_data['password'],
                )
                group_name = user_data['group']
                if group_name in groups:
                    user.groups.add(groups[group_name])
                    user.save()

                created_count += 1
                self.stdout.write(
                    f"Создан пользователь {user_data['username']} с ID {user_data['id']}"
                )
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f"Ошибка при создании пользователя {user_data['username']}: {e}"
                ))
                continue

        self.stdout.write(f"Создано {created_count} новых пользователей")
