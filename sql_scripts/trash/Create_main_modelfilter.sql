USE planner;

CREATE TABLE [{PLANNER_DB}].[dbo].[main_modelfilter]
([owner] INT PRIMARY KEY NOT NULL,
[schedules] NVARCHAR(100),
[engineers] NVARCHAR(100),
[material_type] NVARCHAR(100),
[work_dates] NVARCHAR(100),
[task_status] NVARCHAR(100));


INSERT INTO [{PLANNER_DB}].[dbo].[main_modelfilter]
([owner], [schedules], [engineers], [material_type], [work_dates], [task_status])
VALUES
(1,	'("2")', '("1")', '("film", "season")', '04/01/2025 - 07/01/2025', '("not_ready", "ready")');