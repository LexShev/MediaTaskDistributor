CREATE TRIGGER filepath_history_trigger
ON task_list
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    -- ��� ����� ������� (INSERT)
    INSERT INTO [{PLANNER_DB}].[dbo].[filepath_history] ([program_id], [file_path], [engineer_id], [duration], [task_status], [time_of_change])
    SELECT i.program_id, i.file_path, i.[engineer_id], i.[duration], i.[task_status], GETDATE()
    FROM inserted i
    WHERE NOT EXISTS (
        SELECT 1 FROM deleted
    );
    -- ��� ����������� ������� (UPDATE), ��� ��������� file_path
    INSERT INTO [{PLANNER_DB}].[dbo].[filepath_history] ([program_id], [file_path], [engineer_id], [duration], [task_status], [time_of_change])
    SELECT i.program_id, i.file_path, i.[engineer_id], i.[duration], i.[task_status], GETDATE()
    FROM inserted i
    JOIN deleted d ON i.program_id = d.program_id
    WHERE i.file_path != d.file_path OR (i.file_path IS NULL AND d.file_path IS NOT NULL) OR (i.file_path IS NOT NULL AND d.file_path IS NULL);
END;