import ast
import json
from datetime import date, datetime

from django.db import connections

from planner.settings import OPLAN_DB, PLANNER_DB
from main.settings.main_settings import main_settings

def check_schedule(schedule_id_str):
    try:
        if not schedule_id_str or schedule_id_str == '[]':
            return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 36)'
        schedule_id_list = [str(x) for x in ast.literal_eval(schedule_id_str)]
        if len(schedule_id_list) == 1:
            return f'AND [schedule_id] = {schedule_id_list[0]}'
        else:
            return f'AND [schedule_id] IN ({", ".join(schedule_id_list)})'
    except Exception as error:
        print(error)
        return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 36)'

def check_date(schedule_date):
    today = date.today()
    if not schedule_date or schedule_date == '':
        return today, today
    try:
        return [datetime.strptime(str_date, '%d.%m.%Y') for str_date in schedule_date.split(' - ')]
    except Exception as error:
        print(error)
        return today, today

def get_schedule_days(field_dict):
    start_date, end_date = check_date(field_dict.get('schedule_date'))
    columns = (('SchedDay', 'schedule_day_id'), ('SchedDay', 'schedule_id'), ('SchedDay', 'day_date'),
               ('SchedDay', 'approved_for_broadcasting'), ('SchedDay', 'last_edit_user_id'), ('SchedDay', 'last_edit_time'),
               ('SchedDay', 'DayStatus'), ('SchedDay', 'DayType'),
               ('Status', 'status'), ('Status', 'last_edit_user_id'), ('Status', 'last_edit_time'),
               ('Comment', 'comment'), ('Comment', 'last_edit_user_id'), ('Comment', 'last_edit_time'),)
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    with connections[OPLAN_DB].cursor() as cursor:
        query = f"""
        SELECT 
            {sql_columns}
        FROM [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
        LEFT JOIN [{PLANNER_DB}].[dbo].[playlist_status] AS Status
            ON SchedDay.[schedule_day_id] = Status.[schedule_day_id]
        LEFT JOIN [{PLANNER_DB}].[dbo].[playlist_comment] AS Comment
            ON SchedDay.[schedule_day_id] = Comment.[schedule_day_id]
        WHERE [day_date] BETWEEN CONVERT(DATE, %s) AND CONVERT(DATE, %s)
        {check_schedule(field_dict.get('schedule_id'))}
        ORDER BY [day_date]
        """

        cursor.execute(query, (start_date, end_date))
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(django_columns, row)))
        return results

def choose_type_query(query):
    schedule_day_id = query.get('schedule_day_id')
    schedule_id = query.get('schedule_id')
    schedule_day_date = query.get('schedule_day_date')

    if schedule_day_id is not None:
        params = (schedule_day_id, )
        sql_condition = 'AND SchedProg.[schedule_day_id] = %s'

    else:
        params = (schedule_id, schedule_day_date)
        sql_condition = """
        AND SchedDay.[schedule_id] = %s
        AND SchedDay.[day_date] = CONVERT(DATE, %s)
        """
    return sql_condition, params

def get_schedule_list(query):
    sql_condition, params = choose_type_query(query)
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
            SELECT SchedProg.[schedule_day_id]
                  ,SchedProg.[program_id]
                  ,[start_time]
                  ,SchedProg.[duration] AS SchedProg_duration
                  ,MaterialProg.[duration] AS MaterialProg_duration
                  ,[ad_duration]
                  ,SchedProg.[name]
                  ,[can_be_moved]
                  ,[can_be_inserted]
                  ,[scheduled_program_id]
                  ,[ParentID]
                  ,[SlotType]
                  ,MaterialProg.[MaterialTypeID]
                  ,[MaterialID]
                  ,[PlannedStartTime]
                  ,[IsBlock]
                  ,[Level]
                  ,SchedProg.[program_type_id] AS SchedProg_type_id
                  ,MaterialProg.[program_type_id] AS MaterialProg_type_id
                  ,[TheAir]
                  ,[Active]
                  ,[Premiere]
                  ,[ChildPosition]
                  ,[DateTime]
                  ,[LastEditUser]
                  ,[CreatedAt]
                  ,[CreatedBy]
                  ,[LastEditTime]
                  ,[LastPlacementPosition]
                  ,[MediumName]
                  ,[Verified]
                  ,Progs.[SuitableMaterialForScheduleID] AS SuitableMaterial
                  ,Task.[task_status]
                  ,CASE 
                       WHEN EXISTS (
                         SELECT 1 
                         FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] AS ProgCustField
                         WHERE ProgCustField.[ObjectId] = SchedProg.[program_id]
                           AND ProgCustField.[ProgramCustomFieldId] IN (7, 15)
                       ) THEN 1 
                       ELSE 0 
                    END AS oplan_ready
              FROM [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
              LEFT JOIN [oplan3].[dbo].[program] AS Progs
                ON SchedProg.[program_id] = Progs.[program_id]
              LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON SchedProg.[program_id] = Task.[program_id]
              LEFT JOIN [oplan3].[dbo].[program] AS MaterialProg
                ON Progs.[SuitableMaterialForScheduleID] = MaterialProg.[program_id]
              LEFT JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
              WHERE SchedProg.[Deleted] = 0
              AND NOT (SchedProg.[SlotType] = 2 AND SchedProg.[Level] = 3)
              {sql_condition}
              AND SchedProg.[DeletedIncludeParent] = 0
              AND SchedProg.[TheAir] = 1
              ORDER BY [DateTime], [Level], [ChildPosition]
            '''

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        schedule_data = data_transformation(columns, cursor.fetchall())

    return build_hierarchy_from_level(schedule_data)

def build_hierarchy_from_level(schedule_data):
    nodes = {}

    # Создаем все узлы
    for item in schedule_data:
        nodes[item['scheduled_program_id']] = {**item, 'children': []}

    # Строим дерево
    root_items = []

    for item in schedule_data:
        node = nodes[item['scheduled_program_id']]
        parent_id = item.get('ParentID')

        if parent_id is not None and parent_id in nodes:
            nodes[parent_id]['children'].append(node)
        else:
            root_items.append(node)

    # Сортируем детей по ChildPosition
    def sort_children(node):
        node['children'].sort(key=lambda x: x.get('ChildPosition', 0))
        for child in node['children']:
            sort_children(child)

    for root in root_items:
        sort_children(root)

    return root_items

def data_transformation(columns, results):
    workers_dict = main_settings.get_oplan_workers_dict()
    data = []
    for row in results:
        temp_dict = dict(zip(columns, row))

        sched_prog_type_id = temp_dict.get('SchedProg_type_id')
        mat_prog_type_id = temp_dict.get('MaterialProg_type_id')
        task_status = temp_dict.get('task_status')
        mat_prog_duration = temp_dict.get('MaterialProg_duration')
        sched_prog_duration = temp_dict.get('SchedProg_duration')
        slot_type = temp_dict.get('SlotType')

        temp_dict['CreatedByName'] = workers_dict.get(temp_dict['CreatedBy'], '')

        if sched_prog_duration is not None:
            temp_dict['duration'] = sched_prog_duration
        elif sched_prog_duration is None and mat_prog_duration is not None:
            temp_dict['duration'] = mat_prog_duration
        else:
            temp_dict['duration'] = None

        if sched_prog_type_id is not None:
            temp_dict['program_type_id'] = sched_prog_type_id
        elif sched_prog_type_id is None and mat_prog_type_id is not None:
            temp_dict['program_type_id'] = mat_prog_type_id
        else:
            temp_dict['program_type_id'] = None

        if temp_dict.get('MaterialTypeID'):
            # TODO:
            pass

        temp_dict['type'] = check_type(slot_type, temp_dict.get('IsBlock'), temp_dict['program_type_id'], task_status)

        if task_status == 'final':
            temp_dict['is_ready'] = True
        elif not task_status and temp_dict.get('oplan_ready'):
            temp_dict['is_ready'] = True
        else:
            temp_dict['is_ready'] = False

        if task_status == 'no_material':
            temp_dict['color'] = 'no-material'
        else:
            temp_dict['color'] = color_dict.get(temp_dict.get('program_type_id', 0))

        temp_dict['graphics'] = get_graphics_rules()

        temp_dict['graphics_level'] = 1

        data.append(temp_dict)

    return data

def get_graphics_rules():
    graphics_list = [
        {
            "id": "g1",
            "name": "air_now",
            "alias": "Сейчас в эфире",
            "programId": "prog1",
            "start": 21600,
            "end": 21660,
            "level": 2,
            "duration": "постоянно"
        }
    ]
    return json.dumps(graphics_list, ensure_ascii=False, separators=(',', ':'))

def check_type(slot_type, is_block, program_type_id, task_status):
    program_type_id_list = [1, 2, 4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20]
    if slot_type == 2:
        return 'segment'
    elif slot_type == 1 and is_block:
        return 'block'
    elif program_type_id in program_type_id_list or task_status == 'no_material':
        return 'program'
    elif program_type_id == 9:
        return 'advert'
    elif program_type_id == 15:
        return 'license'
    return 'other'

color_dict = {
    None: '',
    0: '',
    1: 'bg-light-subtle',
    2: 'bg-light-subtle',
    3: 'bg-primary-subtle',
    4: 'bg-success-subtle',
    5: 'bg-success-subtle',
    6: 'bg-success-subtle',
    7: 'bg-warning-subtle',
    8: 'bg-warning-subtle',
    9: 'bg-primary-subtle',
    10: 'bg-danger-subtle',
    11: 'bg-danger-subtle',
    12: 'bg-danger-subtle',
    13: '',
    14: 'bg-info-subtle',
    15: 'bg-info-subtle',
    16: '',
    17: '',
    18: '',
    19: 'bg-warning-subtle',
    20: 'bg-warning-subtle',
}

'''
1	Программа
2	Программа сети
3	Реклама
4	Сериал
5	Фильм
6	Мультфильм
7	Фильм с цензурой
8	Сериал с цензурой
9	Promo
10	Фильм с субтитрами
11	Мультфильм с субтитрами
12	Сериал с субтитрами
13	Заглушка
14	Рекламная скобка
15	Лицензия
16	Короткометражка
17	Спецролик
18	Социалка
19	Мультфильм с цензурой
20	Короткометражка с цензурой
'''
