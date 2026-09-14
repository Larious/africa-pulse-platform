-- SYNTHETIC DEMONSTRATION ONLY. Domain views derive from the seeded scenario.

-- Mobility and commercial provision
SELECT m.city_name, avg(m.trips) AS daily_trips, avg(c.commercial_services / c.population * 100000) AS services_per_100k FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.commercial c USING (scenario_id, city_id, local_date) GROUP BY m.city_name;

-- Rainfall and mobility
SELECT m.city_name, count() AS paired_days, corr(e.rainfall_mm, m.congestion_ratio) AS correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) GROUP BY m.city_name;

-- Air pressure and mobility
SELECT m.city_name, avg(e.pm2_5) AS pm2_5, avg(e.nitrogen_dioxide) AS no2, corr(e.pm2_5, m.congestion_ratio) AS correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) GROUP BY m.city_name;

-- Fuel costs and transport activity
SELECT m.city_name, avg(k.fuel_local_per_litre / k.usd_rate * 8) AS fuel_usd_per_100km, corr(k.fuel_local_per_litre / k.usd_rate, m.trips) AS fuel_trip_correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.market k USING (scenario_id, city_id, local_date) GROUP BY m.city_name;

-- Service provision and air quality
SELECT m.city_name, avg(c.commercial_services / c.population * 100000) AS services_per_100k, avg(e.pm2_5) AS pm2_5 FROM synthetic_demo.commercial c INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) INNER JOIN synthetic_demo.mobility m USING (scenario_id, city_id, local_date) GROUP BY m.city_name;