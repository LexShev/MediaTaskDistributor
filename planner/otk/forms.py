from django import forms
from django.db import connections

from .models import OtkModel


def db_engineers():
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT [ItemsString]
        FROM [oplan3].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] = 15
        '''
        cursor.execute(query)
        engineers_list = cursor.fetchone()
    if engineers_list:
        return engineers_list[0]


engineers_list = db_engineers()
engineers = [('', '-')]
if engineers_list:
    for engineer in enumerate(engineers_list.split('\r\n')):
        if engineer[1]:
            engineers.append(engineer)

class OtkForm(forms.ModelForm):
    class Meta:
        model = OtkModel
        fields = ('ready_date', 'sched_date', 'engineer_id', 'material_type', 'schedule_id', 'task_status')
        labels = {'ready_date': 'Дата отсмотра',
                  'sched_date': 'Дата эфира',
                  'engineer_id': 'Выполняет',
                  'material_type': 'Тип материала',
                  'schedule_id': 'Канал',
                  'task_status': 'Статус задачи'}

        task_status = [('', '-'),
                       ('not_ready', 'Не готов'),
                       ('ready', 'Отсмотрен'),
                       ('fix', 'На доработке')]

        material_type = [('', '-'),
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]

        widgets = {
            'ready_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "ready_date"}, format='%Y-%m-%d'),
            'sched_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "sched_date"}, format='%Y-%m-%d'),
            'engineer_id': forms.Select(
                attrs={'class': "form-select", 'id': "engineer_id"}, choices=engineers),
            'material_type': forms.Select(
                attrs={'class': "form-select", 'id': "material_type"}, choices=material_type),
            'schedule_id': forms.Select(
                attrs={'class': "form-select", 'id': "schedule_id"}, choices=task_status),
            'task_status': forms.Select(
                attrs={'class': "form-select", 'id': "task_status"}, choices=task_status),
        }

