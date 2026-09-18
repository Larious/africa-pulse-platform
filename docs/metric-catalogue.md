# Metric Catalogue

| Metric | Grain | Definition | Quality and limitation |
|---|---|---|---|
| Median congestion ratio | City/local day | Median of `1 - current_speed_kph / free_flow_speed_kph` across valid configured road samples | A selected-road traffic proxy, not ridership or city-wide vehicle volume. Published with sample coverage. |
| Valid road-sample coverage | City/local day | Distinct valid road samples divided by configured road samples | Detects incomplete sampling; it does not establish city-wide coverage. |
| Average PM2.5 | City/local day | Mean of modelled PM2.5 snapshots at the city reference coordinate | Modelled estimate, not a ground-station network result. |
| Total precipitation | City/local day | Sum of source precipitation snapshots in millimetres | Represents the configured coordinate and source cadence. |
| USD rate | Currency/local city day | Latest USD-to-NGN or USD-to-ZAR snapshot for the day | Native quote convention is quote currency per USD. |
| Country inflation context | City/local day | Latest World Bank `FP.CPI.TOTL.ZG` value for the city's country | Country-level context, never a city measurement. |
| Commercial category count | City/category/snapshot | Count of deduplicated OpenStreetMap entities in the configured candidate area | Not density until approved city boundary and population denominator are supplied. |
| City Intelligence Score | City/local day | Weighted 0-100 components when eligibility rules are met | Currently unavailable: current live mobility coverage is absent for Lagos/Abuja, no approved commercial denominator exists, and history is insufficient. |
