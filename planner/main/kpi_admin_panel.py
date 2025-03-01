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

def kpi_info_dict(work_date, workers):
    if isinstance(workers, int):
        workers = (workers, workers)
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
        WHERE Task.[work_date] = '{work_date}'
        AND Task.[worker_id] IN {workers}
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        # task_list = [dict(zip(django_columns, task)) for task in result]
        task_list = []
        total_duration = 0
        total_count = 0
        ready_tasks = 0
        for task in result:
            task_dict = dict(zip(django_columns, task))
            task_list.append(task_dict)
            total_duration += task_dict['Task_duration']
            total_count += 1
            if task_dict['Task_task_status'] == 'ready':
                ready_tasks += 1
        not_ready_tasks = total_count - ready_tasks
        summary_dict = {'total_count': total_count, 'ready_tasks': ready_tasks, 'not_ready_tasks': not_ready_tasks,
                        'total_duration': total_duration, 'date': datetime.datetime.now()}
    return {'task_list': task_list, 'summary_dict': summary_dict}
