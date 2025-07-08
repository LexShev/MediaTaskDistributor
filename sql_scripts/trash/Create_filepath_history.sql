USE planner;
 
CREATE TABLE filepath_history
(
	history_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	file_path NVARCHAR(MAX) NOT NULL,
	engineer_id INT NOT NULL,
	duration INT,
	task_status NVARCHAR(30),
	time_of_change DATETIME NOT NULL,
);