from django.db import connections
import datetime
from planner.settings import OPLAN_DB, PLANNER_DB

def parent_adult_name(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Progs.[program_id], Progs.[parent_id], Adult.[Name]
        FROM [{OPLAN_DB}].[dbo].[program] AS Progs
        LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        adult_name = cursor.fetchone()
    if adult_name:
        if adult_name[2]:
            return adult_name[2]
        elif not adult_name[2] and adult_name[1]:
            return parent_adult_name(adult_name[1])
    return ''


def calc_deadline(task_date):
    return task_date - datetime.timedelta(days=14)

def fast_search(program_name) -> list:
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                       ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                       ('Progs', 'duration'), ('Adult', 'Name'), ('Task', 'worker_id'), ('Task', 'sched_id'),
                       ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status')]
            sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
            django_columns = [f'{col}_{val}' for col, val in columns]
            query = f'''
            SELECT TOP (500) {sql_columns}
            FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Task.[program_id] = Progs.[program_id]
            LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
                ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
            WHERE Progs.[deleted] = 0
            AND Progs.[name] LIKE '%{program_name}%'
            ORDER BY Progs.[name];
            '''
            cursor.execute(query)
            result = cursor.fetchall()
        search_list = [dict(zip(django_columns, task)) for task in result]
        for temp_dict in search_list:
            if not temp_dict.get('Adult_Name'):
                temp_dict['Adult_Name'] = parent_adult_name(temp_dict.get('Progs_parent_id'))
            temp_dict['Task_deadline'] = calc_deadline(temp_dict['Task_sched_date'])
        return search_list
    except Exception as error:
        print(error)
        return []


