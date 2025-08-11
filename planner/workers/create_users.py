import json

from django.contrib.auth.models import User, Group

def create_users_in_groups():
    groups = {
        'moderators': Group.objects.get_or_create(name='moderators')[0],
        'preparation_engineers': Group.objects.get_or_create(name='preparation_engineers')[0],
        'broadcast_engineers': Group.objects.get_or_create(name='broadcast_engineers')[0],
        'otk_engineers': Group.objects.get_or_create(name='otk_engineers')[0]
    }

    with open('planner/workers/.users.json', 'r', encoding='utf-8') as f:
        users_data = json.load(f)

        for user_data in users_data:
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

        print(f"Создано {len(users_data)} пользователей в разных группах")

