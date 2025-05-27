WITH LatestPrograms AS (
    SELECT TOP 3 
        m.[program_id]
    FROM 
        [planner].[dbo].[messenger_static_message] m
    GROUP BY 
        m.[program_id]
    ORDER BY 
        MAX(m.[timestamp]) DESC
)

SELECT 
    m.[message_id],
    m.[owner],
    m.[program_id],
    m.[message],
    m.[timestamp],
    m.[file_path],
	Progs.[name],
	CASE 
        WHEN v.[message_id] IS NOT NULL THEN CAST(1 AS BIT) -- True (read)
        ELSE CAST(0 AS BIT) -- False (unread)
    END AS [read]
FROM 
    [planner].[dbo].[messenger_static_message] AS m
LEFT JOIN [planner].[dbo].[messenger_static_messageviews] AS v
    ON m.[message_id] = v.[message_id] AND v.[worker_id] = 3
LEFT JOIN [oplan3].[dbo].[program] AS Progs
        ON m.[program_id] = Progs.[program_id]
WHERE m.[program_id] IN (SELECT [program_id] FROM LatestPrograms)
ORDER BY 
    m.[program_id],
    m.[timestamp] DESC;