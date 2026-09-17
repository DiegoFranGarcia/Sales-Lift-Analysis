-- Raw landing tables. Types chosen to accept the CSVs as-is;
-- cleaning happens in the panel build, not here.

DROP TABLE IF EXISTS raw_train;
DROP TABLE IF EXISTS raw_store;

CREATE TABLE raw_train (
    store           INTEGER     NOT NULL,
    day_of_week     SMALLINT    NOT NULL,
    date            DATE        NOT NULL,
    sales           INTEGER     NOT NULL,
    customers       INTEGER     NOT NULL,
    open            SMALLINT    NOT NULL,
    promo           SMALLINT    NOT NULL,
    state_holiday   TEXT        NOT NULL,   -- mixed '0'/'a'/'b'/'c'; TEXT on purpose
    school_holiday  SMALLINT    NOT NULL
);

CREATE TABLE raw_store (
    store                         INTEGER PRIMARY KEY,
    store_type                    TEXT,
    assortment                    TEXT,
    competition_distance          NUMERIC,
    competition_open_since_month  SMALLINT,
    competition_open_since_year   SMALLINT,
    promo2                        SMALLINT,
    promo2_since_week             SMALLINT,
    promo2_since_year             SMALLINT,
    promo_interval                TEXT
);