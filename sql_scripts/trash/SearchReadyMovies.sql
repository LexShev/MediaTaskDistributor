SELECT Progs.[program_id], Progs.[parent_id], Progs.[name], Sched.[schedule_name], Progs.[program_type_id]
    FROM [{OPLAN_DB}].[dbo].[File] AS Files
    JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
        ON Files.[ClipID] = Clips.[ClipID]
    JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
        ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
    JOIN [{OPLAN_DB}].[dbo].[program_type] AS Types
        ON Progs.[program_type_id] = Types.[program_type_id]
    JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
        ON Progs.[program_id] = SchedProg.[program_id]
    JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
        ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
    JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
        ON SchedDay.[schedule_id] = Sched.[schedule_id]
	LEFT JOIN [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] AS Val
		ON Progs.[program_id] = Val.[ObjectId]
	LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
        ON Progs.[program_id] = Task.[program_id]
    WHERE Files.[Deleted] = 0
    AND Files.[PhysicallyDeleted] = 0
    AND Clips.[Deleted] = 0
    AND Progs.[deleted] = 0
	AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
    AND SchedDay.[day_date] IN ('2025-02-13', '2025-02-13')
    AND Progs.[program_id] > 0
	AND Val.[ProgramCustomFieldId] = 15
    ORDER BY Sched.[schedule_name]