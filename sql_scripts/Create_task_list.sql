USE planner;
 
CREATE TABLE task_list
(
    program_id INT PRIMARY KEY NOT NULL,
    engineer_id INT NOT NULL,
    duration INT NOT NULL,
	work_date DATE NOT NULL,
	ready_date DATE,
	task_status NVARCHAR(30) NOT NULL,
	file_path NVARCHAR(MAX),
);