# Decision Log

## ADR-001: Use one TomTom traffic-flow source for all cities

**Decision:** Use TomTom Traffic Flow as the initial mobility source for Lagos, Abuja, and Cape Town.

**Reason:** It returned the same road-level fields for all three cities during three live validation windows. A single provider makes the congestion proxy comparable across the portfolio.

**Trade-off:** It measures sampled road conditions, not passenger demand, fare revenue, or public-transport ridership.

## ADR-002: Store TomTom metadata and normalised measures, not full payloads

**Decision:** Retain request fingerprint, response checksum, source context, and normalised traffic fields while full-payload retention remains subject to terms review.

**Reason:** This preserves traceability without assuming the account permits long-term storage of complete provider responses.

## ADR-003: Use two-hour source collection

**Decision:** Poll the 15 currently validated TomTom road samples every two hours.

**Reason:** The free plan provides 20,000 calls per month. Ten planned samples per city at 12 runs per day use about 10,800 calls per month; hourly polling would exceed the quota before retries.

## ADR-004: Treat initial commercial areas as candidate bounding boxes

**Decision:** Use documented bounding boxes for the first OpenStreetMap snapshot, named `candidate_area_bbox_v1`.

**Reason:** They allow an initial reproducible source integration before approved municipal boundary files are supplied.

**Trade-off:** Counts are not city-census values and must not be compared as density until a boundary and population denominator are approved.

## ADR-005: Recover Overpass requests through POST

**Incident:** The initial URL-encoded Overpass GET for the Lagos candidate area returned HTTP 406.

**Decision:** Use a POST request with a descriptive project user agent.

**Result:** The rerun completed and stored 15 category-level commercial snapshots across three cities. The failed run remains in `control.ingestion_run`; no commercial facts were inserted by the failed attempt.

## ADR-006: Keep World Bank measures at country grain

**Decision:** Store World Bank official exchange-rate and inflation releases by country, indicator, and reference year.

**Reason:** The source is periodic country context. Joining it to a city mart does not turn it into a city observation.
