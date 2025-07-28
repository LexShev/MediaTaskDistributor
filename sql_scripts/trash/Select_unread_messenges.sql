SELECT 
    m.[message_id],
    m.[owner],
    m.[program_id],
    m.[message],
    m.[timestamp],
    m.[file_path]
FROM 
    [{PLANNER_DB}].[dbo].[messenger_static_message] AS m
LEFT JOIN [{PLANNER_DB}].[dbo].[messenger_static_messageviews] AS v
    ON m.[message_id] = v.[message_id] AND v.[worker_id] = 3
WHERE 
    v.[message_id] IS NULL
ORDER BY 
    m.[program_id],
    m.[timestamp] DESC;