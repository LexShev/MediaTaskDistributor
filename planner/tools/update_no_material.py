from django.db import connections

from messenger_static.messenger_utils import create_notification
from planner.settings import PLANNER_DB, OPLAN_DB


def get_no_material_list():
    success_list = []
    error_list = []
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            f'''
            SELECT Task.[program_id], Task.[worker_id]
            FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Task.[program_id] = Progs.[program_id]
            WHERE Task.[task_status] = 'no_material'
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            '''
        )
        no_material_list = cursor.fetchall()
        if no_material_list:
            for program_id, worker_id in no_material_list:
                try:
                    cursor.execute(
                        f'''
                        UPDATE Task
                        SET Task.[task_status] = 'not_ready',
                            Task.[file_path] = Files.[Name],
                            Task.[duration] = Progs.[duration]
                        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
                        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs 
                            ON Task.[program_id] = Progs.[program_id]
                        JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips 
                            ON Progs.[SuitableMaterialForScheduleID] = Clips.[MaterialID]
                        JOIN [{OPLAN_DB}].[dbo].[File] AS Files 
                            ON Clips.[ClipID] = Files.[ClipID]
                        WHERE Task.[program_id] = %s
                            AND Files.[Deleted] = 0
                            AND Files.[PhysicallyDeleted] = 0
                            AND Files.[Name] IS NOT NULL
                            AND Clips.[Deleted] = 0
                            AND Progs.[deleted] = 0
                            AND Progs.[DeletedIncludeParent] = 0
                        ''', (program_id,)
                    )
                    create_notification(
                        {'sender': 0, 'recipient': worker_id, 'program_id': program_id,
                         'message': 'Появился недостающий медиафайл',
                         'comment': 'Статус материала изменился\nМатериал отсутствует -> Не готов'}
                    )
                    success_list.append(program_id)
                except Exception as e:
                    error_list.append(program_id)
                    print(e)
    return success_list, error_list
