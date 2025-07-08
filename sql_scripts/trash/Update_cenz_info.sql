UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
SET [TextValue] = (CASE
	WHEN ([ProgramCustomFieldId] = 5) THEN 'Приключенческий боевик с Крисом Хемсвортом. Группа моряков борется за выживание в открытом океане.'
	WHEN ([ProgramCustomFieldId] = 12) THEN 'mat' END),
[DateValue] = (CASE
	WHEN ([ProgramCustomFieldId] = 7) THEN '2023-03-28 00:00:00.000' END),
[IntValue] = (CASE
	WHEN ([ProgramCustomFieldId] = 14) THEN 3
	WHEN ([ProgramCustomFieldId] = 15) THEN 0 END)
WHERE [ObjectId] = 6794
AND [ProgramCustomFieldId] != 5
