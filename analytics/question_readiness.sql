-- Evidence gates for the seven business questions in the project brief.
-- A row marked `not_ready` is an honest result, not a failed query.

WITH
    today() AS today_date,
    (SELECT countDistinct(local_date) FROM mart.city_mobility_daily FINAL) AS mobility_days,
    (SELECT countDistinct(local_date) FROM mart.city_climate_environment_daily FINAL) AS climate_days,
    (SELECT countDistinct(local_date) FROM mart.city_economic_daily FINAL) AS fx_days,
    (SELECT count() FROM warehouse.fact_commercial_poi_snapshot FINAL) AS commercial_snapshots
SELECT
    'mobility_and_commercial_activity' AS question_id,
    if(commercial_snapshots > 0, 'partial', 'not_ready') AS answer_status,
    'Mobility is a sampled congestion proxy; commercial counts are not density without an approved boundary and population denominator.' AS evidence_or_blocker
UNION ALL
SELECT
    'weather_and_mobility_relationship',
    if(least(mobility_days, climate_days) >= 28, 'ready_for_descriptive_analysis', 'not_ready'),
    concat('Requires 28 shared local days; currently mobility_days=', toString(mobility_days), ', climate_days=', toString(climate_days), '.')
UNION ALL
SELECT
    'environmental_pressure',
    if(climate_days > 0, 'partial', 'not_ready'),
    'Available as modelled PM2.5, PM10, and NO2 at each configured reference coordinate; not a ground-station city-wide measure.'
UNION ALL
SELECT
    'currency_and_fuel_transport_economics',
    'not_ready',
    'FX exists, but no permitted fuel-market source has been integrated. Add a documented official or licensed fuel-price source before analysis.'
UNION ALL
SELECT
    'commercial_services_relative_to_population',
    'not_ready',
    'Requires an approved municipal boundary, a population denominator with reference date, and comparable commercial coverage.'
UNION ALL
SELECT
    'improving_or_deteriorating_over_time',
    if(mobility_days >= 28, 'ready_for_descriptive_analysis', 'not_ready'),
    concat('Requires 28 local days; currently mobility_days=', toString(mobility_days), '.')
UNION ALL
SELECT
    'defensible_city_intelligence_score',
    if(fx_days >= 7 AND mobility_days >= 28, 'pending_governance_inputs', 'not_ready'),
    concat('Requires approved commercial denominator, seven FX days, and 28 trend days; currently fx_days=', toString(fx_days), ', mobility_days=', toString(mobility_days), '.');
