USE planner;
 
CREATE TABLE filepath_history
(
	program_id INT PRIMARY KEY IDENTITY NOT NULL,
	worker_id INT NOT NULL,
	task_status NVARCHAR(30),
	comment NVARCHAR(MAX),
	time_of_change DATETIME NOT NULL,
);