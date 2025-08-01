USE planner;
 
CREATE TABLE permission_list
(
	[permission_group] NVARCHAR(50) NOT NULL,
	[home] BIT NOT NULL,
	[day] BIT NOT NULL,
	[on_air_report] BIT NOT NULL,
	[week] BIT NOT NULL,
	[list] BIT NOT NULL,
	[kpi_info] BIT NOT NULL,
	[work_calendar] BIT NOT NULL,
	[common_pool] BIT NOT NULL,
	[full_info_card] BIT NOT NULL,
	[otk] BIT NOT NULL,
	[advanced_search] BIT NOT NULL,
	[task_manager] BIT NOT NULL,
	[messenger] BIT NOT NULL,
	[desktop] BIT NOT NULL,
);

INSERT INTO [{PLANNER_DB}].[dbo].[permission_list]
([permission_group], [home], [day], [on_air_report], [week], [list], [kpi_info], [work_calendar], [common_pool], [full_info_card], [otk], [advanced_search], [task_manager], [messenger], [desktop])
VALUES 
('admin', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('preparation_engineer', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('broadcast_engineer', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('otk_engineer', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('editor', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1);