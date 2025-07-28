SELECT Progs.[program_id], Progs.[parent_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Sched.[schedule_name], SchedDay.[day_date]
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
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Sched.[channel_id] IN (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
            AND SchedDay.[day_date] IN ('2025-03-01', '2025-03-02', '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07', '2025-03-08', '2025-03-09', '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14', '2025-03-15', '2025-03-16', '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21')
            AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] ASC
