USE planner;
 

CREATE TABLE [days_off]
(
	[day_off] DATE,
);

INSERT INTO [planner].[dbo].[days_off]
VALUES 
(convert(date, '2025-02-27')),
(convert(date, '2025-02-28'));
