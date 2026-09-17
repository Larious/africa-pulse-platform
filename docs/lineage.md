# Metric Lineage

## Example: Daily median congestion ratio

1. A TomTom request is made for a configured road sample in `config/cities.yaml`.
2. The connector records the request fingerprint, response checksum, source ID, received time, HTTP status, and run ID in `control.raw_evidence`.
3. The connector standardises speed and travel-time fields. The validation rules write their result to `quality.rule_result`.
4. Valid values enter `warehouse.fact_traffic_flow_observation` with the same source ID, run ID, road-sample ID, and response checksum.
5. `mart.city_mobility_daily` will calculate a city-local-day median of `1 - current_speed_kph / free_flow_speed_kph` and publish valid-sample coverage plus average source confidence.

This path is deliberately traceable without storing a TomTom payload until its terms are approved. For public sources, the evidence row also includes an ignored local raw JSON path and a checksum that identifies the exact replay input.
