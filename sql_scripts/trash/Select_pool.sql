SELECT Progs.[program_id], Progs.[parent_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration]
FROM [{OPLAN_DB}].[dbo].[program] AS Progs
WHERE Progs.[deleted] = 0
AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
AND Progs.[program_kind] IN (0, 3)
AND Progs.[program_id] NOT IN
	(SELECT Task.[program_id] FROM [{PLANNER_DB}].[dbo].[task_list] AS Task)
AND Progs.[program_id] NOT IN
	(SELECT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
	WHERE [ProgramCustomFieldId] = 15)
