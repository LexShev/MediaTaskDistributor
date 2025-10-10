import json
import os.path

from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from planner.settings import BASE_DIR


def create_users_in_groups():
    groups = {
        'moderators': Group.objects.get_or_create(name='moderators')[0],
        'preparation_engineers': Group.objects.get_or_create(name='preparation_engineers')[0],
        'broadcast_engineers': Group.objects.get_or_create(name='broadcast_engineers')[0],
        'otk_engineers': Group.objects.get_or_create(name='otk_engineers')[0],
        'editors': Group.objects.get_or_create(name='editors')[0],
    }

    with open(os.path.join(BASE_DIR, 'workers/.users.json'), 'r', encoding='utf-8') as f:
        users_data = json.load(f)
        created_count = 0
        for user_data in users_data:
            if User.objects.filter(id=user_data['id']).exists():
                print(f"Пользователь с ID {user_data['id']} уже существует, пропускаем")
                continue

            if User.objects.filter(username=user_data['username']).exists():
                print(f"Пользователь {user_data['username']} уже существует, пропускаем")
                continue
            try:
                user = User.objects.create_user(
                    id=user_data['id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                group_name = user_data['group']
                if group_name in groups:
                    user.groups.add(groups[group_name])
                    user.save()

                created_count += 1
                print(f"Создан пользователь {user_data['username']} с ID {user_data['id']}")
            except IntegrityError as e:
                print(f"Ошибка при создании пользователя {user_data['username']}: {e}")
                continue

            print(f"Создано {created_count} новых пользователей")

        print(f"Создано {len(users_data)} пользователей в разных группах")

