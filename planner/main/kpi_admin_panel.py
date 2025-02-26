from django.db import connections

def convert_fr_to_tf(frames, fps=25):
    sec = frames/fps
    hh = int(sec // 3600)
    mm = int((sec % 3600) // 60)
    ss = int((sec % 3600) % 60 // 1)
    ff = int(sec % 1 * fps)
    tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:03}'
    return tf

def kpi_info_dict(work_date):
    with connections['planner'].cursor() as cursor:
        columns = 'program_id', 'worker_id', 'worker', 'duration', 'work_date', 'task_status'
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list]
        WHERE [work_date] = '{work_date}'
        '''
        cursor.execute(query)
        task_list = [dict(zip(columns, task)) for task in cursor.fetchall()]
        # task_list = [convert_fr_to_tf(task['duration']) for task in task_list]
        print(task_list)
    return task_list
