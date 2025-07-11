from datetime import datetime, timedelta, date

from django.db import connections


def main_distribution():
    work_date = datetime.today().date()
    # work_date = date(day=7, month=7, year=2025)

    material_list_sql, django_columns = oplan_material_list(start_date=work_date, work_duration=28)
    program_id_list = []
    for i, program_info in enumerate(material_list_sql, 1):
        print('working', i)
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        program_id_list.append(program_id)

        temp_dict = dict(zip(django_columns, program_info))

        sched_id = temp_dict.get('SchedDay_schedule_id')
        sched_date = temp_dict.get('SchedDay_day_date')
        duration = temp_dict.get('Progs_duration')
        suitable_material = temp_dict.get('Progs_SuitableMaterialForScheduleID')

        engineer_id, kpi, work_date = date_seek(work_date, duration)

        if suitable_material:
            file_path = find_file_path(program_id)
            status = 'not_ready'
        else:
            file_path = ''
            status = 'no_material'
        insert_film(program_id, engineer_id, duration, sched_id, sched_date, work_date, status, file_path)
    return 'success'


def oplan_material_list(start_date, work_duration, program_type=(4, 5, 6, 10, 11, 12)):
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Progs', 'SuitableMaterialForScheduleID'), ('SchedDay', 'day_date')
    ]
    with connections['oplan3'].cursor() as cursor:
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [oplan3].[dbo].[program] AS Progs
            JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [oplan3].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [planner].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] BETWEEN '{start_date}' AND DATEADD(DAY, {work_duration}, '{start_date}')
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues] WHERE [ProgramCustomFieldId] = 15)
            AND Progs.[program_id] NOT IN
                (SELECT [program_id] FROM [planner].[dbo].[task_list])
            AND Task.[engineer_id] IS NULL
            ORDER BY SchedProg.[DateTime] {order}
            """
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def find_file_path(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT Files.[Name]
        FROM [oplan3].[dbo].[File] AS Files
        JOIN [oplan3].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        file_path = cursor.fetchone()
    if file_path:
        return file_path[0]

def date_seek(work_date, duration):
    kpi_info = kpi_min(work_date)
    if kpi_info:
        for engineer_id, kpi in kpi_info:
            new_kpi = kpi + (duration / 720000.0)
            if new_kpi <= 1:
                return engineer_id, kpi, work_date
    print('work_date', work_date)
    work_date += timedelta(days=1)
    return date_seek(work_date, duration)

def kpi_min_obsolete(work_date):
    kpi_list = []
    with connections['planner'].cursor() as cursor:
        query_01 = f'''
        SELECT [worker_id]
        FROM [planner].[dbo].[worker_list]
        WHERE '{work_date}' NOT IN (SELECT day_off FROM [planner].[dbo].[days_off])
        AND [fired] = 'False'
        '''
        cursor.execute(query_01)
        engineer_list = cursor.fetchall()

        if engineer_list:
            for engineer in engineer_list:
                engineer_id = engineer[0]
                query_02 = f'''
                SELECT Task.[engineer_id], Task.[duration]
                FROM [planner].[dbo].[task_list] AS Task
                WHERE Task.[work_date] = '{work_date}'
                AND Task.[engineer_id] = '{engineer_id}'
                '''
                cursor.execute(query_02)
                kpi = sum([duration for engineer_id, duration in cursor.fetchall()])/720000.0
                kpi_list.append((engineer_id, kpi))
    return sorted(kpi_list, key=lambda x: x[1])

def kpi_min_obsolette_2(work_date):
    with connections['planner'].cursor() as cursor:
        query = '''
        SELECT Worker.[worker_id] AS engineer_id, CAST(COALESCE(SUM(Task.[duration]), 0) AS FLOAT) / 720000.0 AS kpi
        FROM [planner].[dbo].[worker_list] AS Worker
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Worker.[worker_id] = Task.[engineer_id] 
            AND Task.[work_date] = %s
        WHERE %s NOT IN (SELECT day_off FROM [planner].[dbo].[days_off])
        AND [fired] = 'False'
        GROUP BY Worker.[worker_id]
        ORDER BY kpi ASC
        '''
        cursor.execute(query, (work_date, work_date))
        res = cursor.fetchall()
        print('res', res)
        return res

def kpi_min(work_date):
    with connections['planner'].cursor() as cursor:
        query = '''
        DECLARE @target_date DATE
        SET @target_date = %s
        SELECT
            w.[worker_id] AS engineer_id,
            CASE
                WHEN d.[day_off] IS NOT NULL THEN NULL
                WHEN v.[vacation_id] IS NOT NULL THEN NULL
                ELSE CAST(COALESCE(SUM(t.[duration]), 0) AS FLOAT) / 720000.0
            END AS kpi
        FROM
            [planner].[dbo].[worker_list] w
        LEFT JOIN
            [planner].[dbo].[task_list] t ON w.[worker_id] = t.[engineer_id]
            AND t.[work_date] = CONVERT(DATE, @target_date)
        LEFT JOIN
            [planner].[dbo].[days_off] d ON d.[day_off] = CONVERT(DATE, @target_date)
        LEFT JOIN
            [planner].[dbo].[vacation_schedule] v ON w.[worker_id] = v.[worker_id]
            AND CONVERT(DATE, @target_date) BETWEEN v.[start_date] AND v.[end_date]
        WHERE
            w.[fired] = 0
        GROUP BY
            w.[worker_id],
            d.[day_off],
            v.[vacation_id]
        ORDER BY
            kpi ASC;
        '''
        cursor.execute(query, (work_date,))
        res = cursor.fetchall()
        return sorted([item for item in res if item[1] is not None], key=lambda x: x[1])

def insert_film(program_id, engineer_id, duration, sched_id, sched_date, work_date, task_status, file_path=''):
    with connections['planner'].cursor() as cursor:
        columns = '[program_id], [engineer_id], [duration], [sched_id], [sched_date], [work_date], [task_status], [file_path]'
        values = (program_id, engineer_id, duration, sched_id, sched_date, work_date, task_status, file_path)
        query = f'''
        INSERT INTO [planner].[dbo].[task_list] ({columns})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, values)
        print(cursor.rowcount)
        # print(f'{program_id}, {engineer_id} successfully added')

def planner_engineer(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''
        SELECT engineer_id
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        planner_engineer_id = cursor.fetchone()
        if planner_engineer_id:
            return planner_engineer_id[0]
        else:
            return None

def oplan3_engineer(program_id):
    with connections['oplan3'].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [oplan3].[dbo].[ProgramCustomFieldValues] 
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        oplan3_engineer_id = cursor.fetchone()
        if oplan3_engineer_id:
            return oplan3_engineer_id[0]

