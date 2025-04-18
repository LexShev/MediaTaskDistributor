from django.db import connections


def check_value(key, value):
    if value:
        return f"AND Task.[{key}] = '{value}'"
    else:
        return ''

def task_info(field_dict):
    # args = check_value(field_info)
    # fields = ('ready_date', 'sched_date', 'engineer_id', 'material_type', 'sched_id', 'task_status')
    # schedule_id = field_dict.get('schedule_id')
    with connections['planner'].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        {check_value('ready_date', field_dict.get('ready_date'))}
        {check_value('sched_date', field_dict.get('sched_date'))}
        {check_value('engineer_id', field_dict.get('engineer_id'))}
        {check_value('sched_id', field_dict.get('sched_id'))}
        {check_value('task_status', field_dict.get('task_status'))}
        ORDER BY Task.[work_date];
        '''
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result]

'''
        AND Task.[ready_date] = "{field_dict.get('work_dates')}"
        AND Task.[sched_date] = "{field_dict.get('sched_date')}"
        AND Task.[engineer_id] = {field_dict.get('engineer_id')}
        AND Task.[material_type] = {field_dict.get('material_type')}
        AND Task.[schedule_id] {field_dict.get('schedule_id', 'IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)')}
        AND Task.[task_status] = {field_dict.get('task_status')}
        '''