SELECT TOP (1000) Task.[program_id]
      ,Task.[engineer_id] AS Planner_Engineer
      ,CustField.[IntValue] AS Oplan_Engineer
      ,Task.[duration]
      ,[sched_id]
      ,[sched_date]
      ,[work_date]
      ,[ready_date]
      ,[task_status]
      ,[file_path]
  FROM [planner].[dbo].[task_list] AS Task
  LEFT JOIN [oplan3].[dbo].[program] AS Progs
    ON Task.[program_id] = Progs.[program_id]
  LEFT JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS CustField
    ON Progs.[program_id] = CustField.[ObjectId]
  WHERE CustField.[ProgramCustomFieldId] = 15
  AND Task.[engineer_id] != CustField.[IntValue]


SELECT Task.[program_id]
      ,Task.[engineer_id]
      ,Task.[duration]
      ,Task.[sched_id]
      ,Task.[sched_date]
      ,Task.[work_date]
      ,Task.[ready_date]
      ,Task.[task_status]
      ,Task.[file_path]
  FROM [planner].[dbo].[task_list] AS Task
  WHERE Task.[program_id] not IN
  (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
    WHERE [ProgramCustomFieldId] = 7)
  AND Task.[task_status] IN ('ready', 'otk', 'otk_fail', 'final', 'final_fail')