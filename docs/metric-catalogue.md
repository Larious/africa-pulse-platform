# Metric Catalogue

| Metric | Grain | Numerator / denominator or formula | Filters and required inputs | Quality and limitation |
|---|---|---|---|---|
| Median congestion ratio | City/local day | Median of `1 - current_speed_kph / free_flow_speed_kph`; no denominator beyond each valid free-flow speed | Valid traffic rules only; configured road samples for that city and local day | Selected-road traffic proxy, not ridership or city-wide volume. |
| Valid road-sample coverage | City/local day | Distinct valid road samples / configured road samples × 100 | Same city and local day; denominator comes from `dim_road_sample` | Detects incomplete sampling; it does not establish city-wide coverage. |
| Average PM2.5 | City/local day | Sum of valid PM2.5 values / valid air-quality observations | City reference coordinate and valid non-negative values | Modelled estimate, not a ground-station network result. |
| Total precipitation | City/local day | Sum of precipitation millimetres | City reference coordinate and selected observation day | Represents the configured coordinate and source cadence. |
| USD rate | Currency/local city day | Latest quote-currency units per USD | Target currency must be NGN or ZAR; latest valid observation that day | Does not create a historical series before platform launch. |
| Country inflation context | City/local day | World Bank `FP.CPI.TOTL.ZG` value for the latest available reference year | Joined by country code, not city; latest published release | Country-level context, never a city measurement. |
| Commercial category count | City/category/snapshot | Count of deduplicated OpenStreetMap entities; density denominator is intentionally absent | Candidate-area bounding box and category at snapshot time | Not population density until an approved boundary and population denominator exist. |
| City Intelligence Score | City/local day | Weighted sum of five 0–100 components: mobility 30%, commercial 20%, environment 20%, market 15%, direction 15% | Requires approved denominators, history, freshness, and coverage gates | Numeric score is withheld when any publication gate fails. |
