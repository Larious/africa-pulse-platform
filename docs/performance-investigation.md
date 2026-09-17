# Performance Investigation Protocol

The current initial dataset is too small to claim a meaningful runtime improvement. `analytics/performance_evidence.sql` verifies that city-and-time predicates use the intended month partition, min-max index, and primary-key ordering.

Before final assessment, capture a baseline city/month fact query with query-log `read_rows` and elapsed time. Introduce one measured change only after identifying a bottleneck, such as a projection or aggregate table for the demonstrated workload. Re-run the same query, compare result equivalence, `read_rows`, and elapsed time, then record the before/after values here. Do not claim an optimization without those measurements.
