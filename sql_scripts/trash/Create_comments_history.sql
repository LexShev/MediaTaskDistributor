USE planner;
 
CREATE TABLE comments_history
(
	comment_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	task_status NVARCHAR(30),
	worker_id INT NOT NULL,
	comment NVARCHAR(MAX),
    deadline DATE,
	time_of_change DATETIME NOT NULL,
);