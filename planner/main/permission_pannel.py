from django.db import connections
from planner.settings import PLANNER_DB

def ask_db_permissions(worker_id) -> dict:
    with connections[PLANNER_DB].cursor() as cursor:
        perm_list = ('home', 'day', 'on_air_report', 'week', 'list', 'kpi_info', 'work_calendar', 'common_pool',
                     'full_info_card', 'otk', 'advanced_search', 'task_manager', 'messenger', 'desktop')
        columns = ', '.join([f'[{perm}]' for perm in perm_list])
        query = f'''
        SELECT {columns} FROM [{PLANNER_DB}].[dbo].[auth_user_groups] AS Groups
        JOIN [{PLANNER_DB}].[dbo].[auth_group] AS GroupName
            ON Groups.[group_id] = GroupName.[id]
        JOIN [{PLANNER_DB}].[dbo].[permission_list] AS Perm
            ON GroupName.[name] = Perm.[permission_group]
        WHERE Groups.[user_id] = {worker_id}
        '''
        cursor.execute(query)
        perm_val = cursor.fetchone()
        if perm_val:
            return dict(zip(perm_list, perm_val))
        return {}
