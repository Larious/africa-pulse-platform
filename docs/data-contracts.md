# Data Contracts

## Traffic Flow

`warehouse.fact_traffic_flow_observation` grain: one TomTom response for one configured road sample in one scheduled two-hour collection slot.

Required values: current speed, positive free-flow speed, current travel time, free-flow travel time, confidence in `[0, 1]`, city ID, road-sample ID, source ID, run ID, and observed/received timestamps.

Primary quality rules: `traffic.free_flow_speed_positive`, `traffic.current_speed_non_negative`, and `traffic.confidence_in_range`.

## Weather

`warehouse.fact_weather_observation` grain: one Open-Meteo current weather snapshot for one city reference coordinate and source timestamp.

Required values: temperature in degrees Celsius, precipitation in millimetres, wind speed in kilometres per hour, city ID, source ID, run ID, and observed/received timestamps.

Primary quality rule: `weather.physical_ranges`; temperature must be between -80 and 65 C, and precipitation and wind speed must be non-negative.

## Air Quality

`warehouse.fact_air_quality_observation` grain: one Open-Meteo modelled air-quality snapshot for one city reference coordinate and source timestamp.

Required values: PM2.5, PM10, and nitrogen dioxide in micrograms per cubic metre, city ID, source ID, run ID, and observed/received timestamps.

Primary quality rule: `air_quality.non_negative`.

## FX

`warehouse.fact_fx_rate` grain: one USD-to-quote-currency source snapshot per target currency and scheduled collection slot.

Required values: USD base currency, NGN or ZAR quote currency, positive rate, source ID, run ID, and observed/received timestamps.

Primary quality rule: `fx.rate_positive`.
