# Required Question Coverage Plan

Africa Pulse is built to answer the seven decision questions in the project brief. A platform must distinguish a query that can execute from a conclusion that is supported by evidence. The `analytics/question_readiness.sql` query reports that distinction directly from the warehouse.

## What can be answered today

| Question | Current answer | Required caution |
|---|---|---|
| Strongest mobility and commercial activity | Partial comparison only: sampled congestion and candidate-area commercial counts can be shown together. | Congestion is not total mobility activity, and commercial counts are not density. |
| Weather/rainfall and mobility | Same-day observations can be joined. | Do not infer a relationship until 28 shared local days exist. |
| Greatest environmental pressure | Cities can be compared using modelled PM2.5, PM10, and NO2. | This is reference-coordinate model output, not city-wide ground monitoring. |
| Currency and fuel effects | FX snapshots and country inflation context are available. | Fuel-market conditions are absent, so transportation-economics conclusions are not supported. |
| Commercial services relative to population | Not answerable. | Candidate boxes and counts lack an approved population denominator. |
| Improvement or deterioration | Not answerable. | A trend requires at least 28 local days. |
| Defensible City Intelligence Score | Not answerable as a final score. | The score remains `unavailable` until every published gate is met. |

## Changes required to answer every question

### 1. Fuel-market condition source

Add a source only after confirming its access terms, attribution, geographic grain, and release schedule. For each observation, capture:

```text
country_or_city_id, fuel_product, price_per_litre, currency_code,
reference_date, observed_at, source_id, run_id, response_sha256
```

Use a regulator, national statistics office, or licensed provider. Nigeria and South Africa should not be forced into one source if that would make their price definitions incomparable. If source definitions differ, retain the country-specific contract and show the comparison limitation.

The implementation steps are: add a source-register entry and data contract, create a fuel fact table, create a connector and quality rule for non-negative prices and supported currency, join the daily economic mart, and add an analytical query that reports descriptive association only. Do not claim causation from observational FX, fuel, and congestion data.

### 2. Approved city boundary and population inputs

Obtain a versioned municipal boundary for Lagos, Abuja, and Cape Town plus a population source, reference date, and geographic alignment review. Then calculate commercial categories per approved area and per population. Keep `boundary_version`, `population_source`, and `population_reference_date` in the resulting fact or dimension.

The existing OpenStreetMap candidate-area counts must remain separate from this approved-density measure. They cannot be relabelled as city-wide density.

### 3. Observation history

Keep the fast collection schedule running. At 7 days, evaluate FX stability. At 28 shared local days, run descriptive weather/mobility and trend analysis. The platform should report observation counts, road-sample coverage, and source freshness alongside every chart.

### 4. Score publication gate

Publish a score only when all of these hold:

1. Approved commercial boundary and population denominator are present.
2. At least 7 consecutive days of FX observations are available.
3. At least 28 local days of required trend observations are available.
4. Weighted component coverage is at least 80%.
5. No required source is stale beyond its documented service level.

Until then, use component-level metrics and `score_status = 'unavailable'`.

## How to demonstrate this to a reviewer

Run `analytics/question_readiness.sql` in ClickHouse before presenting an analytical conclusion. Then use `analytics/business_questions.sql` only for rows whose readiness status supports the relevant analysis. This protects decision-makers from a dashboard that looks complete while its evidence is incomplete.
