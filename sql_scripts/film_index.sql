-- Схема модуля film_index (Planner MSSQL).
-- Идемпотентно: можно применять повторно.
USE planner;
GO

IF OBJECT_ID('dbo.film_material_index', 'U') IS NULL
CREATE TABLE dbo.film_material_index (
    oplan_program_id INT       NOT NULL CONSTRAINT PK_fmi PRIMARY KEY,
    kinopoisk_id     INT       NULL,
    has_file         BIT       NOT NULL CONSTRAINT DF_fmi_hasfile DEFAULT (0),
    duration_frames  INT       NULL,
    refreshed_at     DATETIME2 NOT NULL CONSTRAINT DF_fmi_refreshed DEFAULT (SYSDATETIME())
);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_fmi_kp' AND object_id = OBJECT_ID('dbo.film_material_index')
)
CREATE INDEX IX_fmi_kp ON dbo.film_material_index (kinopoisk_id);
GO

IF COL_LENGTH('dbo.film_material_index', 'match_source') IS NULL
ALTER TABLE dbo.film_material_index ADD match_source VARCHAR(10) NULL;
GO

IF OBJECT_ID('dbo.film_match_staging', 'U') IS NULL
CREATE TABLE dbo.film_match_staging (
    id               BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_fms PRIMARY KEY,
    run_id           UNIQUEIDENTIFIER NOT NULL,
    oplan_program_id INT       NOT NULL,
    candidate_kp_id  INT       NULL,
    score            FLOAT     NULL,
    title_score      FLOAT     NULL,
    year_score       FLOAT     NULL,
    country_score    FLOAT     NULL,
    bucket           VARCHAR(20) NOT NULL,
    reason           NVARCHAR(300) NULL,
    created_at       DATETIME2 NOT NULL CONSTRAINT DF_fms_created DEFAULT (SYSDATETIME())
);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_fms_run' AND object_id = OBJECT_ID('dbo.film_match_staging')
)
CREATE INDEX IX_fms_run ON dbo.film_match_staging (run_id, oplan_program_id);
GO

IF OBJECT_ID('dbo.film_match_review', 'U') IS NULL
CREATE TABLE dbo.film_match_review (
    id               BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_fmr PRIMARY KEY,
    oplan_program_id INT       NOT NULL,
    run_id           UNIQUEIDENTIFIER NULL,
    candidates_json  NVARCHAR(MAX) NULL,
    status           VARCHAR(20) NOT NULL CONSTRAINT DF_fmr_status DEFAULT ('pending'),
    resolved_kp_id   INT       NULL,
    resolved_by      INT       NULL,
    updated_at       DATETIME2 NOT NULL CONSTRAINT DF_fmr_updated DEFAULT (SYSDATETIME())
);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_fmr_program' AND object_id = OBJECT_ID('dbo.film_match_review')
)
CREATE INDEX IX_fmr_program ON dbo.film_match_review (oplan_program_id, status);
GO

IF COL_LENGTH('dbo.film_match_review', 'bucket') IS NULL
ALTER TABLE dbo.film_match_review ADD bucket VARCHAR(20) NULL;
GO

IF OBJECT_ID('dbo.film_match_run', 'U') IS NULL
CREATE TABLE dbo.film_match_run (
    id            UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_fmr_run PRIMARY KEY,
    started_at    DATETIME2 NOT NULL CONSTRAINT DF_fmrun_started DEFAULT (SYSDATETIME()),
    finished_at   DATETIME2 NULL,
    mode          VARCHAR(20) NULL,
    sample_size   INT NULL,
    total_targets INT NULL,
    auto_high     INT NULL,
    band          INT NULL,
    ambiguous     INT NULL,
    unmatched     INT NULL,
    notes         NVARCHAR(MAX) NULL
);
GO
