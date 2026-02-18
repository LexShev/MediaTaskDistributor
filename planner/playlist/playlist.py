from datetime import date, datetime

from django.db import connections
from django.http import JsonResponse

from main.helpers import oplan_workers_dict
from planner.settings import OPLAN_DB, PLANNER_DB


def check_schedule(schedule_id):
    try:
        if not schedule_id:
            return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 36)'
        return f'AND [schedule_id] = {schedule_id}'
    except Exception as error:
        print(error)
        return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 36)'

def check_date(schedule_date):
    today = date.today()
    if not schedule_date or schedule_date == '[]':
        return today, today
    try:
        return [datetime.strptime(str_date, '%d.%m.%Y') for str_date in schedule_date.split(' - ')]
    except Exception as error:
        print(error)
        return today, today

def get_schedule_days(field_dict):
    start_date, end_date = check_date(field_dict.get('schedule_date'))
    with connections[OPLAN_DB].cursor() as cursor:
        query = f"""
        SELECT 
            [schedule_day_id],
            [schedule_id],
            [day_date],
            [approved_for_broadcasting],
            [last_edit_user_id],
            [last_edit_time],
            [DayStatus],
            [AdvertImportDay],
            [PromoImportDay],
            [MusicImportDay],
            [AdvertListImportDay],
            [DayType]
        FROM [{OPLAN_DB}].[dbo].[schedule_day]
        WHERE [day_date] BETWEEN CONVERT(DATE, %s) AND CONVERT(DATE, %s)
        {check_schedule(field_dict.get('schedule_id'))}
        ORDER BY [day_date]
        """

        cursor.execute(query, (start_date, end_date))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

def get_schedule_list_by_id(schedule_day_id):
    workers_dict = oplan_workers_dict()
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT [schedule_day_id]
              ,SchedProg.[program_id]
              ,[start_time]
              ,SchedProg.[duration]
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
              ,SchedProg.[program_type_id]
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
          WHERE [schedule_day_id] = %s
          AND SchedProg.[Deleted] = 0
          AND SchedProg.[DeletedIncludeParent] = 0
          AND SchedProg.[TheAir] = 1
          ORDER BY [DateTime], [Level], [ChildPosition]
        '''

        cursor.execute(query, (schedule_day_id,))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            temp_dict = dict(zip(columns, row))

            temp_dict['CreatedByName'] = workers_dict.get(temp_dict['CreatedBy'], '')
            results.append(temp_dict)
    return build_hierarchy_from_level(results)


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

def get_schedule_list_by_date(schedule_id, schedule_date):
    workers_dict = oplan_workers_dict()
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
            SELECT SchedProg.[schedule_day_id]
                  ,SchedProg.[program_id]
                  ,[start_time]
                  ,SchedProg.[duration]
                  ,[ad_duration]
                  ,SchedProg.[name]
                  ,[can_be_moved]
                  ,[can_be_inserted]
                  ,[scheduled_program_id]
                  ,[ParentID]
                  ,[SlotType]
                  ,[MaterialID]
                  ,[PlannedStartTime]
                  ,[IsBlock]
                  ,[Level]
                  ,SchedProg.[program_type_id]
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
              LEFT JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
              WHERE SchedProg.[Deleted] = 0
              AND SchedDay.[schedule_id] = %s
              AND SchedDay.[day_date] = CONVERT(DATE, %s)
              AND SchedProg.[DeletedIncludeParent] = 0
              AND SchedProg.[TheAir] = 1
              ORDER BY [DateTime], [Level], [ChildPosition]
            '''

        cursor.execute(query, (schedule_id, schedule_date))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            temp_dict = dict(zip(columns, row))

            temp_dict['CreatedByName'] = workers_dict.get(temp_dict['CreatedBy'], '')
            results.append(temp_dict)
        print('results', results)
    return build_hierarchy_from_level(results)

def create_nested_structure(flat_list, parent_field='ParentID', id_field='scheduled_program_id'):
    """
    Универсальная функция для создания вложенной структуры

    Args:
        flat_list: плоский список словарей
        parent_field: поле, указывающее на родителя
        id_field: поле с уникальным ID

    Returns:
        Вложенный список словарей с ключом 'children'
    """
    # Создаем словарь для быстрого поиска
    item_dict = {item[id_field]: item for item in flat_list}

    # Добавляем пустой список детей каждому элементу
    for item in flat_list:
        item['children'] = []

    # Строим дерево
    root_items = []

    for item in flat_list:
        parent_id = item.get(parent_field)

        if parent_id is None:
            # Это корневой элемент
            root_items.append(item)
        else:
            # Находим родителя
            parent = item_dict.get(parent_id)
            if parent:
                parent['children'].append(item)
            else:
                # Родитель не найден - возможно ошибка данных
                # Добавляем как корневой элемент
                root_items.append(item)

    # Опционально: сортируем детей по какому-либо полю
    # def sort_children(items, sort_key='ChildPosition'):
    #     for item in items:
    #         if item['children']:
    #             item['children'].sort(key=lambda x: x.get(sort_key, 0))
    #             sort_children(item['children'], sort_key)
    #
    # sort_children(root_items)

    return root_items