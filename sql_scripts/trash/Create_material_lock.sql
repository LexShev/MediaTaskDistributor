USE planner;
 
CREATE TABLE material_lock
(
    program_id INT PRIMARY KEY NOT NULL,
	lock_type NVARCHAR(30),
    worker_id INT NOT NULL,
	lock_time DATETIME NOT NULL,
);