DO $do$
BEGIN
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO django_listener, cinema_atlas, kinopoisk_parser_bot',
        current_database()
    );
END
$do$;

REVOKE ALL ON SCHEMA kinopoisk FROM PUBLIC;
REVOKE ALL ON SCHEMA sync FROM PUBLIC;

GRANT USAGE ON SCHEMA kinopoisk TO django_listener, cinema_atlas, kinopoisk_parser_bot;

GRANT SELECT ON TABLE
    kinopoisk.titles,
    kinopoisk.title_payload,
    kinopoisk.title_search
TO django_listener;

GRANT SELECT ON TABLE kinopoisk.titles TO cinema_atlas;

GRANT USAGE ON SCHEMA sync TO kinopoisk_parser_bot;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLE
    kinopoisk.titles,
    kinopoisk.title_payload,
    kinopoisk.title_search
TO kinopoisk_parser_bot;
GRANT SELECT, INSERT ON TABLE sync.runs TO kinopoisk_parser_bot;
GRANT USAGE, SELECT ON SEQUENCE sync.runs_id_seq TO kinopoisk_parser_bot;
