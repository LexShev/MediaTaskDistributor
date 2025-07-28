DECLARE @date DATE
SET @date = '2025-02-25';


SELECT Task.[worker_id], Task.[worker], COALESCE(SUM(Task.[duration])/720000.0, 0) AS KPI
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        WHERE Task.[worker_id] IN
            (SELECT Worker.[worker_id]
            FROM [{PLANNER_DB}].[dbo].[worker_list] AS Worker
            WHERE @date NOT IN (SELECT day_off FROM [{PLANNER_DB}].[dbo].[days_off])
            AND Worker.[fired] = 'False')
        AND Task.[work_date] = @date
        GROUP BY Task.[worker_id], Task.[worker]