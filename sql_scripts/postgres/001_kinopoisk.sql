CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS kinopoisk;
CREATE SCHEMA IF NOT EXISTS sync;

CREATE TABLE IF NOT EXISTS kinopoisk.titles (
    kp_id                integer PRIMARY KEY,
    imdb_id              text,
    tmdb_id              integer,
    type                 text NOT NULL CHECK (type IN ('film', 'series')),
    ru_name              text,
    eng_name             text,
    original_name        text,
    year                 smallint,
    start_year           smallint,
    end_year             smallint,
    status               text,
    duration_min         integer,
    country              text[] NOT NULL DEFAULT '{}',
    genre                text[] NOT NULL DEFAULT '{}',
    keywords             text[] NOT NULL DEFAULT '{}',
    production_companies text[] NOT NULL DEFAULT '{}',
    director_names       text[] NOT NULL DEFAULT '{}',
    kp_rating            numeric(3,1),
    imdb_rating          numeric(3,1),
    tmdb_rating          numeric(3,1),
    poster_url           text,
    poster_url_preview   text,
    short_description    text,
    description          text,
    slogan               text,
    budget               text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    content_hash         text NOT NULL
);

CREATE TABLE IF NOT EXISTS kinopoisk.title_payload (
    kp_id   integer PRIMARY KEY
            REFERENCES kinopoisk.titles(kp_id) ON DELETE CASCADE,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS kinopoisk.title_search (
    kp_id       integer PRIMARY KEY
                REFERENCES kinopoisk.titles(kp_id) ON DELETE CASCADE,
    search_text text NOT NULL,
    type        text NOT NULL,
    year        smallint,
    kp_rating   numeric(3,1)
);

CREATE INDEX IF NOT EXISTS titles_type_year_idx
    ON kinopoisk.titles (type, year);
CREATE INDEX IF NOT EXISTS titles_imdb_id_idx
    ON kinopoisk.titles (imdb_id) WHERE imdb_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS titles_tmdb_id_idx
    ON kinopoisk.titles (tmdb_id) WHERE tmdb_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS titles_country_gin_idx
    ON kinopoisk.titles USING gin (country);
CREATE INDEX IF NOT EXISTS titles_genre_gin_idx
    ON kinopoisk.titles USING gin (genre);
CREATE INDEX IF NOT EXISTS titles_director_gin_idx
    ON kinopoisk.titles USING gin (director_names);
CREATE INDEX IF NOT EXISTS title_search_trgm_idx
    ON kinopoisk.title_search USING gin (search_text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS title_search_type_year_idx
    ON kinopoisk.title_search (type, year);

CREATE TABLE IF NOT EXISTS sync.runs (
    id            bigserial PRIMARY KEY,
    source        text NOT NULL,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    status        text NOT NULL,
    rows_read     bigint NOT NULL DEFAULT 0,
    rows_written  bigint NOT NULL DEFAULT 0,
    error         text
);
