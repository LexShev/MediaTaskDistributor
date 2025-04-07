USE planner;

CREATE TABLE [planner].[dbo].[main_modelfilter]
([owner] INT PRIMARY KEY NOT NULL,
[channels] NVARCHAR(100),
[engineers] NVARCHAR(100),
[material_type] NVARCHAR(100),
[work_dates] DATE,
[task_status] NVARCHAR(100));


INSERT INTO [planner].[dbo].[main_modelfilter]
([owner], [channels], [engineers], [material_type], [work_dates], [task_status])
VALUES
(1,	'2', '1', 'film', '2025-03-10', 'not_ready');