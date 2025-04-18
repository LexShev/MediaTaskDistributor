from django.db.models import Model, Manager, IntegerField, TextField, DateField, CharField, TextChoices
from django.db import connections
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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




class FormChoices(Model):
    class SchedulesID(TextChoices):
        all = "", _("-")
        kre = 3, _('Крепкое'),
        pla = 5, _('Планета дети'),
        mir = 6, _('Мировой сериал'),
        muz = 7, _('Мужской сериал'),
        nas = 8, _('Наше детство'),
        rom = 9, _('Романтичный сериал'),
        nash = 10, _('Наше родное кино'),
        sem = 11, _('Семейное кино'),
        sov = 12, _('Советское родное кино'),
        kin = 20, _('Кино +')

    schedules_id = CharField(
        max_length=2,
        choices=SchedulesID,
        default=SchedulesID.all,
    )

    class Rate(TextChoices):
        all = "", _("-")
        null = 0, _('0+'),
        one = 1, _('6+'),
        two = 2, _('12+'),
        three = 3, _('16+'),
        four = 4, _('18+')

    rate = CharField(
        max_length=2,
        choices=Rate,
        default=Rate.all,
    )

    class Engineers:
        engineers_list = db_engineers()
        choices = [('', '-')]
        if engineers_list:
            for engineer in enumerate(engineers_list.split('\r\n')):
                if engineer[1]:
                    choices.append(engineer)


class OtkModel(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    ready_date = DateField(default=timezone.now, null=True, blank=True)
    sched_date = DateField(default=timezone.now, null=True, blank=True)
    engineer_id = IntegerField(default=1, null=True, blank=True)
    material_type = CharField(max_length=50, null=True, blank=True, default='film')
    sched_id = IntegerField(default=1, null=True, blank=True)
    task_status = CharField(max_length=50, null=True, blank=True, default='ready')