USE planner;
 
CREATE TABLE history_list
(
    action_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	CustomFieldID INT NOT NULL,
	action_description NVARCHAR(MAX),
	action_comment NVARCHAR(MAX),
    worker_id INT NOT NULL,
	time_of_change DATETIME NOT NULL,
	old_value NVARCHAR(MAX),
	new_value NVARCHAR(MAX)
);