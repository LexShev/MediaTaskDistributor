def engineers_wrong_task():
    '''
    SELECT TOP (1000) Task.[program_id]
      ,Task.[engineer_id] AS Planner_Engineer
      ,CustField.[IntValue] AS Oplan_Engineer
      ,Task.[duration]
      ,[sched_id]
      ,[sched_date]
      ,[work_date]
      ,[ready_date]
      ,[task_status]
      ,[file_path]
      FROM [planner].[dbo].[task_list] AS Task
      LEFT JOIN [oplan3].[dbo].[program] AS Progs
        ON Task.[program_id] = Progs.[program_id]
      LEFT JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS CustField
        ON Progs.[program_id] = CustField.[ObjectId]
      WHERE CustField.[ProgramCustomFieldId] = 15
      AND Task.[engineer_id] != CustField.[IntValue]
    '''
    pass

def wrong_oplan_completion():
    '''
    SELECT Task.[program_id]
      ,Task.[engineer_id]
      ,Task.[duration]
      ,Task.[sched_id]
      ,Task.[sched_date]
      ,Task.[work_date]
      ,Task.[ready_date]
      ,Task.[task_status]
      ,Task.[file_path]
      FROM [planner].[dbo].[task_list] AS Task
      WHERE Task.[program_id] not IN
      (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ProgramCustomFieldId] = 7)
      AND Task.[task_status] IN ('ready', 'otk', 'otk_fail', 'final', 'final_fail')
    '''
    pass

def undistributed_tasks():
    '''
    DECLARE @current_date DATE = '2025-10-08'

    SELECT
        Progs.[program_id],
        Task.[task_status],
        CustField.[ProgramCustomFieldId],
        CASE
            WHEN Task.[task_status] IS NOT NULL THEN 'Есть в task_list'
            WHEN CustField.[ProgramCustomFieldId] = 15 THEN 'Есть в CustomField'
            ELSE 'Нет нигде'
        END AS status_info
    FROM [oplan3].[dbo].[program] AS Progs
    JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
        ON Progs.[program_id] = SchedProg.[program_id]
    JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
        ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
    JOIN [oplan3].[dbo].[schedule] AS Sched
        ON SchedDay.[schedule_id] = Sched.[schedule_id]
    LEFT JOIN [planner].[dbo].[task_list] AS Task
        ON Progs.[program_id] = Task.[program_id]
    LEFT JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS CustField
        ON Progs.[program_id] = CustField.[ObjectId]
        AND CustField.[ProgramCustomFieldId] = 15
    WHERE SchedDay.[day_date] = @current_date
    AND Progs.[program_id] > 0
    AND Progs.[deleted] = 0
    AND Progs.[DeletedIncludeParent] = 0
    AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)
    AND SchedProg.[Deleted] = 0
    ORDER BY Task.[task_status], CustField.[ProgramCustomFieldId]
    '''
    pass