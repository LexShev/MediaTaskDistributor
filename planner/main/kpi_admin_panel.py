import datetime

from django.db import connections
from django.template.defaulttags import register


@register.filter
def convert_frames_to_time(frames, fps=25):
    sec = int(frames)/fps
    dd = int((sec // 3600) // 24)
    hh = int((sec // 3600) % 24)
    mm = int((sec % 3600) // 60)
    ss = int((sec % 3600) % 60 // 1)
    ff = int(sec % 1 * fps)
    tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:02}'
    if dd < 1:
        tf = f'{hh:02}:{mm:02}:{ss:02}'
    else:
        tf = f'{dd:02}д. {hh:02}:{mm:02}:{ss:02}'
    return tf

# @register.filter
# def convert_frames_to_time(frames, fps=25):
#     sec = int(frames)/fps
#     return datetime.timedelta(seconds=sec)

def summary_task_list(work_dates):
    if isinstance(work_dates, str):
        work_dates = (work_dates, work_dates)
    with connections['planner'].cursor() as cursor:
        columns = [('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'worker'), ('Task', 'duration'),
                   ('Task', 'work_date'), ('Task', 'task_status'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'orig_name'), ('Progs', 'keywords'), ('Progs', 'production_year')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Task.[work_date] IN {work_dates}
        AND Task.[worker_id] IN (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        AND Task.[task_status] IN ('not_ready', 'ready', 'fix')
        '''
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result]

def kpi_summary_calc(work_dates, workers, task_status):
    print('task_status', task_status)
    print('workers', workers)
    task_list = summary_task_list(work_dates)
    count_dates = len(set(task.get('Task_work_date') for task in task_list))
    count_workers = len(set(task.get('Task_worker_id') for task in task_list))
    total_count = len(task_list)
    total_dur = sum(task.get('Task_duration') for task in task_list)
    ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'ready', task_list)))
    not_ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'not_ready', task_list)))
    ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'ready')
    not_ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'not_ready')
    try:
        total_kpi = total_dur / (720000.0 * count_dates * count_workers)
        ready_kpi = ready_dur / (720000.0 * count_dates * count_workers)
    except Exception as e:
        total_kpi = 0
        ready_kpi = 0
        print(e)
    summary_dict = {'total_count': total_count, 'total_dur': total_dur, 'ready_tasks': ready_tasks,
                    'not_ready_tasks': not_ready_tasks, 'ready_dur': ready_dur, 'not_ready_dur': not_ready_dur,
                    'total_kpi': total_kpi, 'ready_kpi': ready_kpi}

    if not task_status and workers:
        filtered_task_list = (task for task in task_list if task.get('Task_worker_id') == int(workers))
    elif task_status and not workers:
        filtered_task_list = (task for task in task_list if task.get('Task_task_status') == task_status)
    elif task_status and workers:
        filtered_task_list = (task for task in task_list if task.get('Task_task_status') == task_status and task.get('Task_worker_id') == int(workers))
    else:
        filtered_task_list = task_list
    return filtered_task_list, summary_dict


def personal_task_list(work_dates, worker_id):
    if isinstance(work_dates, str):
        work_dates = (work_dates, work_dates)
    # work_dates = ('2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06')
    with connections['planner'].cursor() as cursor:
        columns = [('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'worker'), ('Task', 'duration'),
                   ('Task', 'work_date'), ('Task', 'task_status'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'orig_name'), ('Progs', 'keywords'), ('Progs', 'production_year')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Task.[work_date] IN {work_dates}
        AND Task.[worker_id] = {worker_id}
        '''
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result]

def kpi_personal_calc(work_date, worker_id, task_status):
    task_list = personal_task_list(work_date, worker_id)
    total_count = len(task_list)
    total_dur = sum(task.get('Task_duration') for task in task_list)
    ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'ready', task_list)))
    not_ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'not_ready', task_list)))
    ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'ready')
    not_ready_dur = sum(task.get('Task_duration') for task in task_list if task.get('Task_task_status') == 'not_ready')
    total_kpi = total_dur / 720000.0
    ready_kpi = ready_dur / 720000.0
    summary_dict = {'total_count': total_count, 'total_dur': total_dur, 'ready_tasks': ready_tasks,
                    'not_ready_tasks': not_ready_tasks, 'ready_dur': ready_dur, 'not_ready_dur': not_ready_dur,
                    'total_kpi': total_kpi, 'ready_kpi': ready_kpi}
    if task_status == "('not_ready', 'ready', 'fix')":
        filtered_task_list = task_list
    else:
        filtered_task_list = (task for task in task_list if task.get('Task_task_status') == task_status)
    return filtered_task_list, summary_dict

# def calc_task_list():
#     real_dates = set(task['Task_work_date'] for task in task_list)
#     summary_list = []
#     for date in dates:
#         filtered_task = list(filter(lambda x: x.get('Task_work_date') == date, task_list))
#
#         total_count = len(filtered_task)
#         total_dur = sum(task.get('Task_duration') for task in filtered_task)
#         ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'ready', filtered_task)))
#         not_ready_tasks = len(list(filter(lambda x: x.get('Task_task_status') == 'not_ready', filtered_task)))
#         ready_dur = sum(task.get('Task_duration') for task in filtered_task if task.get('Task_task_status') == 'ready')
#         not_ready_dur = sum(task.get('Task_duration') for task in filtered_task if task.get('Task_task_status') == 'not_ready')
#         total_kpi = total_dur/720000.0
#         ready_kpi = ready_dur/720000.0
#         summary_dict = {'total_count': total_count, 'total_dur': total_dur, 'ready_tasks': ready_tasks,
#                         'not_ready_tasks': not_ready_tasks, 'ready_dur': ready_dur, 'not_ready_dur': not_ready_dur,
#                         'total_kpi': total_kpi, 'ready_kpi': ready_kpi}
#         print('summary_dict', summary_dict)
#         summary_list.append(summary_dict)
#     return summary_list


def filter_task_list(task_list, date):
    return filter(lambda x: x['Task_work_date'] == date, task_list)
