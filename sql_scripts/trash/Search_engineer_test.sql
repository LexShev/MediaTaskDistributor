 SELECT Progs.[program_id], Progs.[parent_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Adult.[Name], Task.[engineer_id]
FROM [{OPLAN_DB}].[dbo].[program] AS Progs
LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
    ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
	ON Progs.[program_id] = Task.[program_id]
WHERE Progs.[deleted] = 0
AND DeletedIncludeParent = 0
AND [program_kind] IN (0, 3)
AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
AND Task.[engineer_id] = 1
ORDER BY Progs.[name];

SELECT Progs.[program_id], Progs.[parent_id], Progs.[program_type_id], Progs.[name], Progs.[production_year], Progs.[AnonsCaption], Progs.[episode_num], Progs.[duration], Adult.[Name], Val.[IntValue]
FROM [{OPLAN_DB}].[dbo].[program] AS Progs
LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
    ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
LEFT JOIN [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] AS Val
    ON Progs.[program_id] = Val.[ObjectId]
WHERE Progs.[deleted] = 0
AND Val.[ProgramCustomFieldId] = 15
AND Progs.[DeletedIncludeParent] = 0
AND [program_kind] IN (0, 3)
AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
AND Val.[IntValue] = 1
ORDER BY Progs.[name];
