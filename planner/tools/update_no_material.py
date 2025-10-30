from datetime import date
from typing import Dict

from django.db import connections

from main.templatetags.custom_filters import schedule_name
from messenger_static.messenger_utils import create_notification
from planner.settings import PLANNER_DB, OPLAN_DB
from tools.ffmpeg_processing import start_ffmpeg_scanners

def update_sched_date(program_id) -> Dict[str, str]:
    # if program_id != 279438:
    #     return {'status': 'error', 'message': f'Для {program_id} дата эфира не изменялась'}
    try:
        query = f'''
        SELECT Progs.[Name], Task.[sched_id], SchedDay.[schedule_id],
        CONVERT(DATE, Task.[sched_date]), CONVERT(DATE, SchedDay.[day_date]), SchedProg.[Deleted]
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
            ON Progs.[program_id] = SchedProg.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
            ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
        WHERE Task.[program_id] = %s
        ORDER BY SchedDay.[day_date] ASC
        '''
        with connections[OPLAN_DB].cursor() as cursor:
            cursor.execute(query, (program_id,))
            sched_list = cursor.fetchall()
            if not sched_list:
                return {'status': 'error', 'message': f'Для {program_id} дата эфира не изменялась'}
            today = date.today()
            deleted_list = []
            nearest_sched_date = None
            new_schedule_id = None
            for program in sched_list:
                name, task_sched_id, sched_schedule_id, task_sched_date, sched_day_date, is_deleted = program
                if is_deleted and task_sched_date == sched_day_date:
                    deleted_list.append([program_id, name, task_sched_id, sched_schedule_id, task_sched_date, sched_day_date, is_deleted])
                # Ищем ближайшую будущую дату из НЕудалённых
                if not is_deleted and sched_day_date > today:
                    if nearest_sched_date is None or sched_day_date < nearest_sched_date:
                        nearest_sched_date = sched_day_date
                        new_schedule_id = sched_schedule_id
            if deleted_list and nearest_sched_date:
                update_query = f'''
                        DECLARE @new_sched_date DATE
                        SET @new_sched_date = %s
                        UPDATE [{PLANNER_DB}].[dbo].[task_list]
                        SET [sched_date] = @new_sched_date, [deadline] = DATEADD(DAY, -14, @new_sched_date)
                        WHERE [program_id] = %s
                        '''
                cursor.execute(update_query, (nearest_sched_date, program_id))
                print(f"Для программы {name} обновлена дата эфира с {task_sched_date} на {nearest_sched_date}")
            return {'status': 'success',
                    'message': f"Для программы {name} обновлена дата эфира с {task_sched_date} на {nearest_sched_date}",
                    'deleted_list': deleted_list, 'old_sched_date': task_sched_date, 'new_sched_date': nearest_sched_date,
                    'sched_date_changed': task_sched_date != nearest_sched_date,
                    'channel_changed': task_sched_id != new_schedule_id,
                    'old_schedule_id': task_sched_id, 'new_schedule_id': new_schedule_id}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': str(error)}

def get_no_material_list() -> Dict[str, str]:
    success_list = []
    error_list = []
    sched_results = []
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(
            f'''
            SELECT Task.[program_id], Task.[worker_id], Files.[FileID], Files.[Name]
            FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Task.[program_id] = Progs.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            JOIN [{OPLAN_DB}].[dbo].[File] AS Files
                ON Files.[ClipID] = Clips.[ClipID]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Task.[task_status] = 'no_material'
            '''
        )
        no_material_list = cursor.fetchall()
        if no_material_list:
            for program_id, worker_id, file_id, file_path in no_material_list:
                try:
                    start_ffmpeg_scanners(file_id, file_path)
                except Exception as error:
                    print(error)
                try:
                    sched_result = update_sched_date(program_id)
                    sched_results.append(sched_result)
                except Exception as error:
                    print(error)
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
                    comment = 'Статус материала изменился\nМатериал отсутствует -> Не готов\n'
                    if sched_result.get('status') == 'success' and sched_result.get('sched_date_changed'):
                        old_sched_date = sched_result.get('old_sched_date')
                        new_sched_date = sched_result.get('new_sched_date')
                        comment += f'Дата эфира изменилась\n{old_sched_date} -> {new_sched_date}\n'
                    if sched_result.get('channel_changed'):
                        old_schedule_id = schedule_name(sched_result.get('old_schedule_id'))
                        new_schedule_id = schedule_name(sched_result.get('new_schedule_id'))
                        comment += f'Канал изменился\n{old_schedule_id} -> {new_schedule_id}\n'
                    create_notification(
                        {'sender': 0, 'recipient': worker_id, 'program_id': program_id,
                         'message': 'Появился недостающий медиафайл',
                         'comment': comment}
                    )
                    success_list.append([program_id, worker_id, file_id, file_path])
                except Exception as error:
                    print(error)
                    error_list.append([program_id, worker_id, file_id, file_path])
    return {
        'status': 'success', 'message': 'Программы без материала успешно проанализированы', 'success_list': success_list, 'error_list': error_list,
        'sched_results': sched_results}
