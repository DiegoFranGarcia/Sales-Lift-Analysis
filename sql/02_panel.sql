-- =====================================================================
-- Store classification (plan §4)
-- Adoption week = Monday of the ISO week given by Promo2SinceYear/Week.
-- =====================================================================

DROP TABLE IF EXISTS store_classified CASCADE;

CREATE TABLE store_classified AS
WITH bounds AS (
    SELECT MIN(date) AS panel_start, MAX(date) AS panel_end FROM raw_train
),
adoption AS (
    SELECT
        s.store,
        s.store_type,
        s.assortment,
        s.competition_distance,
        s.promo2,
        s.promo_interval,
        CASE
            WHEN s.promo2 = 1
             AND s.promo2_since_year IS NOT NULL
             AND s.promo2_since_week IS NOT NULL
            THEN to_date(
                     s.promo2_since_year::text || '-' ||
                     lpad(s.promo2_since_week::text, 2, '0'),
                     'IYYY-IW'
                 )
        END AS adoption_week
    FROM raw_store s
)
SELECT
    a.*,
    CASE
        WHEN a.promo2 = 0                              THEN 'never_treated'
        WHEN a.adoption_week IS NULL                   THEN 'missing_date'
        WHEN a.adoption_week <  b.panel_start          THEN 'always_treated'
        WHEN a.adoption_week >  b.panel_end            THEN 'post_window'
        ELSE 'in_window'
    END AS treat_group,
    CASE
        WHEN a.adoption_week IS NOT NULL
        THEN date_trunc('quarter', a.adoption_week)::date
    END AS cohort_quarter
FROM adoption a
CROSS JOIN bounds b;

CREATE INDEX ON store_classified (store);


-- =====================================================================
-- Store-week panel (plan §5)
-- Outcome: mean daily sales on OPEN days only, aggregated to ISO week.
-- All stores retained here; sample restrictions (§6) are a later step.
-- =====================================================================

DROP TABLE IF EXISTS store_week CASCADE;

CREATE TABLE store_week AS
SELECT
    t.store,
    date_trunc('week', t.date)::date            AS week_start,

    COUNT(*)                                     AS days_observed,
    COUNT(*) FILTER (WHERE t.open = 1)           AS open_days,

    -- Primary outcome inputs
    SUM(t.sales)     FILTER (WHERE t.open = 1)   AS sales_open,
    SUM(t.customers) FILTER (WHERE t.open = 1)   AS customers_open,

    AVG(t.sales)     FILTER (WHERE t.open = 1)   AS mean_daily_sales,
    AVG(t.customers) FILTER (WHERE t.open = 1)   AS mean_daily_customers,

    -- Secondary outcome: average transaction value
    (SUM(t.sales)     FILTER (WHERE t.open = 1))::numeric
      / NULLIF(SUM(t.customers) FILTER (WHERE t.open = 1), 0)
                                                 AS avg_transaction_value,

    -- Time-varying covariates (plan §4: daily `promo` is NOT the treatment)
    COUNT(*) FILTER (WHERE t.promo = 1)          AS promo_days,
    COUNT(*) FILTER (WHERE t.school_holiday = 1) AS school_holiday_days,
    COUNT(*) FILTER (WHERE t.state_holiday <> '0') AS state_holiday_days
FROM raw_train t
GROUP BY t.store, date_trunc('week', t.date);

CREATE INDEX ON store_week (store, week_start);