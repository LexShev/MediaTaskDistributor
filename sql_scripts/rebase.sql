DECLARE @sql NVARCHAR(MAX) = ''

SELECT @sql = @sql +
    'SELECT * INTO [oplan3_lite].[dbo].[' + name + '] FROM [oplan3].[dbo].[' + name + '];' + CHAR(13)
FROM (VALUES
    ('AdultType'),
    ('Clip'),
    ('File'),
    ('ObjectLock'),
    ('program'),
    ('program_type'),
    ('ProgramCustomFields'),
    ('ProgramCustomFieldValues'),
    ('schedule'),
    ('schedule_day'),
    ('scheduled_program'),
    ('user')
) AS tables(name)

PRINT @sql
EXEC sp_executesql @sql