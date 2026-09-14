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

## Commercial Snapshot

`warehouse.fact_commercial_poi_snapshot` grain: one OpenStreetMap category count for one city candidate area and snapshot time.

Required values: city ID, category, non-negative count, area-definition version, source ID, run ID, snapshot timestamp, and response checksum.

Primary quality rule: `commercial.count_non_negative`. Invalid values are quarantined; valid counts remain explicitly scoped to `candidate_area_bbox_v1` until an approved boundary replaces it.

## Economic Indicator Release

`warehouse.fact_economic_indicator_release` grain: one World Bank country indicator release for one reference year.

Required values: country code, indicator code and name, reference year, finite numeric value, source ID, run ID, received timestamp, and response checksum.

Primary quality rule: `economic.value_present`. A release may arrive after its reference year; both the source reference year and platform received time remain stored.
