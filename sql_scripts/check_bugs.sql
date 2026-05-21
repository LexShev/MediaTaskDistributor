-- Сначала посмотрим, сколько дубликатов
SELECT [ObjectId], [ProgramCustomFieldId], COUNT(*) as cnt
FROM [oplan3].[dbo].[ProgramCustomFieldValues]
GROUP BY [ObjectId], [ProgramCustomFieldId]
HAVING COUNT(*) > 1
ORDER BY cnt DESC

-- Если дубликаты есть — удалить все, кроме одного с минимальным ID
DELETE FROM [oplan3].[dbo].[ProgramCustomFieldValues]
WHERE [ProgramCustomFieldValuesID] NOT IN (
    SELECT MIN([ProgramCustomFieldValuesID])
    FROM [oplan3].[dbo].[ProgramCustomFieldValues]
    GROUP BY [ObjectId], [ProgramCustomFieldId]
)