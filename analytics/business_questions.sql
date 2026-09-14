-- Q1. Executive comparison: joins mobility, environment, economic context, and score coverage.
SELECT mobility.city_id, mobility.local_date, mobility.median_congestion_ratio,
       climate.average_pm2_5_micrograms_per_cubic_metre, economic.usd_rate,
       score.weighted_coverage_pct, score.score_status
FROM mart.city_mobility_daily AS mobility
LEFT JOIN mart.city_climate_environment_daily AS climate USING (city_id, local_date)
LEFT JOIN mart.city_economic_daily AS economic USING (city_id, local_date)
LEFT JOIN mart.city_intelligence_daily AS score USING (city_id, local_date)
ORDER BY mobility.local_date DESC, mobility.city_id;

-- Q2. Mobility and weather: compare local-day congestion with rainfall and temperature.
SELECT mobility.city_id, mobility.local_date, mobility.median_congestion_ratio,
       climate.total_precipitation_mm, climate.average_temperature_celsius,
       mobility.valid_sample_coverage_pct
FROM mart.city_mobility_daily AS mobility
INNER JOIN mart.city_climate_environment_daily AS climate USING (city_id, local_date)
ORDER BY mobility.local_date, mobility.city_id;

-- Q3. Environmental pressure: compare air-quality estimates with traffic congestion.
SELECT climate.city_id, climate.local_date, climate.average_pm2_5_micrograms_per_cubic_metre,
       climate.average_nitrogen_dioxide_micrograms_per_cubic_metre,
       mobility.median_congestion_ratio, mobility.valid_sample_coverage_pct
FROM mart.city_climate_environment_daily AS climate
LEFT JOIN mart.city_mobility_daily AS mobility USING (city_id, local_date)
ORDER BY climate.average_pm2_5_micrograms_per_cubic_metre DESC;

-- Q4. Economic context: USD rates with official country inflation context.
SELECT city_id, local_date, currency_code, usd_rate, latest_country_inflation_pct,
       latest_country_inflation_year
FROM mart.city_economic_daily
ORDER BY local_date DESC, city_id;

-- Q5. Explicit uncertainty: show unsupported score inputs alongside available evidence.
SELECT score.city_id, score.local_date, score.score_status, score.weighted_coverage_pct,
       score.limitation, mobility.valid_sample_coverage_pct,
       climate.air_quality_observations
FROM mart.city_intelligence_daily AS score
LEFT JOIN mart.city_mobility_daily AS mobility USING (city_id, local_date)
LEFT JOIN mart.city_climate_environment_daily AS climate USING (city_id, local_date)
ORDER BY score.local_date DESC, score.city_id;
