SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
WHERE [ProgramCustomFieldId] = 15
AND [ObjectId] IN (SELECT DISTINCT Progs.[program_id]
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
    AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    AND SchedDay.[day_date] BETWEEN '2025-10-01' AND DATEADD(DAY, 28, '2025-10-01')
    AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
    AND Progs.[program_id] > 0
    AND Progs.[program_id] NOT IN
        (SELECT DISTINCT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ProgramCustomFieldId] = 15
        OR [ProgramCustomFieldId] = 7)
    AND Progs.[program_id] NOT IN
        (SELECT [program_id] FROM [planner].[dbo].[task_list])
    AND Task.[engineer_id] IS NULL)