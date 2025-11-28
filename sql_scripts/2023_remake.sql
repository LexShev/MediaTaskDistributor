DECLARE @remake_date DATE
SET @remake_date = '2026-01-01'

-- All ready tasks for 2023 for a sched time @remake date
SELECT DISTINCT Progs.[program_id], Progs.[parent_id], SchedDay.[schedule_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Progs.[SuitableMaterialForScheduleID], SchedDay.[day_date], SchedProg.[DateTime]
    FROM [oplan3].[dbo].[program] AS Progs
    JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
        ON Progs.[program_id] = SchedProg.[program_id]
    JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
        ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
    LEFT JOIN [planner].[dbo].[task_list] AS Task
        ON Progs.[program_id] = Task.[program_id]
    WHERE Progs.[deleted] = 0
    AND Progs.[DeletedIncludeParent] = 0
    AND SchedProg.[Deleted] = 0
    AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    AND SchedDay.[day_date] BETWEEN @remake_date AND DATEADD(DAY, 31, @remake_date)
    AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)
    AND Progs.[program_id] > 0
    AND Progs.[program_id] IN
        (SELECT DISTINCT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [DateValue] BETWEEN CONVERT(DATE, '2023-01-01') AND CONVERT(DATE,'2024-01-01'))
    AND Progs.[program_id] NOT IN
        (SELECT [program_id] FROM [planner].[dbo].[task_list])
    AND Task.[worker_id] IS NULL
    ORDER BY SchedProg.[DateTime] ASC

-- All usual not ready tasks for a sched time @remake date
SELECT DISTINCT Progs.[program_id], Progs.[parent_id], SchedDay.[schedule_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Progs.[SuitableMaterialForScheduleID], SchedDay.[day_date], SchedProg.[DateTime]
    FROM [oplan3].[dbo].[program] AS Progs
    JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
        ON Progs.[program_id] = SchedProg.[program_id]
    JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
        ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
    WHERE Progs.[deleted] = 0
    AND Progs.[DeletedIncludeParent] = 0
    AND SchedProg.[Deleted] = 0
    AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    AND SchedDay.[day_date] BETWEEN @remake_date AND DATEADD(DAY, 31, @remake_date)
    AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12, 16)
    AND Progs.[program_id] > 0
    AND Progs.[program_id] NOT IN
        (SELECT DISTINCT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15
                OR [ProgramCustomFieldId] = 7)
    AND Progs.[program_id] NOT IN
        (SELECT [program_id] FROM [planner].[dbo].[task_list])
    ORDER BY SchedProg.[DateTime] ASC

-- All tasks for a sched time @remake date
SELECT DISTINCT Progs.[program_id], Progs.[parent_id], SchedDay.[schedule_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Progs.[SuitableMaterialForScheduleID], SchedDay.[day_date], SchedProg.[DateTime]
    FROM [oplan3].[dbo].[program] AS Progs
    JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
        ON Progs.[program_id] = SchedProg.[program_id]
    JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
        ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
    WHERE Progs.[deleted] = 0
    AND Progs.[DeletedIncludeParent] = 0
    AND SchedProg.[Deleted] = 0
    AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    AND SchedDay.[day_date] BETWEEN @remake_date AND DATEADD(DAY, 31, @remake_date)
    AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)
    AND Progs.[program_id] > 0
    ORDER BY SchedProg.[DateTime] ASC
