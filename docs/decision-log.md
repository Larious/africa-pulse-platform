# Decision Log

## ADR-001: Use one TomTom traffic-flow source for all cities

**Decision:** Use TomTom Traffic Flow as the initial mobility source for Lagos, Abuja, and Cape Town.

**Reason:** It provides one consistent road-level schema and works for the Cape Town validation points. The current credential returns `Point too far from nearest existing segment` for the configured Lagos and Abuja points, so the platform keeps those observations unavailable until provider coverage or road coordinates are resolved. A single provider remains the preferred comparable design, but coverage is an explicit operational gate.

**Trade-off:** It measures sampled road conditions, not passenger demand, fare revenue, or public-transport ridership.

**Rejected alternatives:** Combining different mobility providers by city would weaken comparability because their coverage, definitions, and update timing differ. A ridership source was not available with the same permitted access and city coverage for all three cities.

## ADR-002: Store TomTom metadata and normalised measures, not full payloads

**Decision:** Retain request fingerprint, response checksum, source context, and normalised traffic fields while full-payload retention remains subject to terms review.

**Reason:** This preserves traceability without assuming the account permits long-term storage of complete provider responses.

**Rejected alternative:** Storing every provider payload indefinitely would improve forensic detail but could violate account terms and increase sensitive-data retention without a documented need.

## ADR-003: Use two-hour source collection

**Decision:** Poll the 15 currently validated TomTom road samples every two hours.

**Reason:** The free plan provides 20,000 calls per month. Ten planned samples per city at 12 runs per day use about 10,800 calls per month; hourly polling would exceed the quota before retries.

**Rejected alternative:** Hourly collection would provide finer temporal resolution but would consume the quota before retries and reduce operational headroom.

## ADR-004: Treat initial commercial areas as candidate bounding boxes

**Decision:** Use documented bounding boxes for the first OpenStreetMap snapshot, named `candidate_area_bbox_v1`.

**Reason:** They allow an initial reproducible source integration before approved municipal boundary files are supplied.

**Trade-off:** Counts are not city-census values and must not be compared as density until a boundary and population denominator are approved.

**Rejected alternative:** Treating the bounding box as a municipal boundary would make the chart look complete but would produce an indefensible denominator and misleading city comparisons.

## ADR-005: Recover Overpass requests through POST

**Incident:** The initial URL-encoded Overpass GET for the Lagos candidate area returned HTTP 406.

**Decision:** Use a POST request with a descriptive project user agent.

**Result:** The rerun completed and stored 15 category-level commercial snapshots across three cities. The failed run remains in `control.ingestion_run`; no commercial facts were inserted by the failed attempt.

## ADR-006: Keep World Bank measures at country grain

**Decision:** Store World Bank official exchange-rate and inflation releases by country, indicator, and reference year.

**Reason:** The source is periodic country context. Joining it to a city mart does not turn it into a city observation.

## ADR-007: Retry transient Overpass failures without masking an outage

**Incident:** On 2026-09-14, a scheduled commercial snapshot encountered an Overpass HTTP 504 timeout, followed by HTTP 429 rate limiting.

**Decision:** Retry transient transport failures and HTTP 429/5xx responses up to three times with bounded backoff. Leave request and schema errors as immediate failures.

**Result:** The collection run remained failed after the provider continued rejecting requests. Ten valid category observations had already been written by the earlier implementation before the third city failed; they remain traceable to the failed run and are not silently deleted. The revised workflow buffers future commercial facts until every city response succeeds. The dashboard marks commercial freshness stale, and no replacement data was invented. The next weekly schedule will retry within the source's published cadence.
