USE planner;
 
CREATE TABLE permission_list
(
	[permission_group] NVARCHAR(50) NOT NULL,
	[day] BIT NOT NULL,
	[month] BIT NOT NULL,
	[week] BIT NOT NULL,
	[list] BIT NOT NULL,
	[kpi_info] BIT NOT NULL,
	[work_calendar] BIT NOT NULL,
	[common_pool] BIT NOT NULL,
	[full_info_card] BIT NOT NULL,
	[advanced_search] BIT NOT NULL,
);

INSERT INTO [planner].[dbo].[permission_list]
([permission_group], [day], [month], [week], [list], [kpi_info], [work_calendar], [common_pool], [full_info_card], [advanced_search])
VALUES 
('admin', 1, 1, 1, 1, 1, 1, 1, 1, 1),
('preparation_engineer', 1, 1, 1, 1, 1, 1, 1, 1, 1),
('broadcast_engineer', 0, 1, 0, 0, 1, 1, 1, 1, 1),
('otk', 0, 1, 0, 0, 1, 1, 1, 1, 1),
('editor', 0, 1, 0, 0, 1, 1, 1, 1, 1);