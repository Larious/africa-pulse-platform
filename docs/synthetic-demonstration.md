# Synthetic Demonstration Environment

The instructor has authorized synthetic data where a legitimate source is unavailable. This environment demonstrates the analytical capabilities that require missing fuel data, approved population denominators, and long observation history. It is not part of the production evidence path.

## Separation rules

- Synthetic rows are stored only in the `synthetic_demo` ClickHouse database.
- Real source facts remain in `warehouse`; real business marts remain in `mart`.
- The synthetic dashboard runs separately on port `8766`; the real dashboard remains on port `8765`.
- Every screen, query result, and presentation reference must say `SYNTHETIC DEMONSTRATION ONLY`.
- Synthetic values must never be described as observed, live, current, forecast, or sourced city facts.

## Run it

```bash
# Creates 105 rows: 35 days x 3 cities, with a fixed seed.
.venv/bin/python -m africa_pulse.synthetic_demo --generate

# Serves the separate synthetic dashboard.
.venv/bin/python -m africa_pulse.synthetic_demo --dashboard
```

Open `http://127.0.0.1:8766` in VS Code Simple Browser. The original real-data dashboard remains `http://127.0.0.1:8765`.

## Scenario assumptions

The deterministic scenario uses seed `20260914` and creates 35 days for Lagos, Abuja, and Cape Town. It includes sampled congestion, rainfall, PM2.5, nitrogen dioxide, USD exchange rate, fuel price, population, commercial service count, commercial services per 100,000 people, an illustrative score, and an improvement/deterioration label.

Numbers are generated from city-specific baseline parameters plus bounded random variation. Rainfall contributes a small positive effect to congestion; fuel prices and FX move gradually; pollution varies with congestion; service density uses fixed illustrative population and commercial-service assumptions. These relationships exist only to test the dashboard and analytical logic. They do not establish causal relationships or represent actual conditions in any city.

## How to present it

Say:

> This is a segregated synthetic scenario, permitted for the capstone to demonstrate missing analytical capability. It shows how the platform calculates fuel-normalized transport context, commercial services per population, 35-day trends, and a fully eligible illustrative score. The real dashboard and warehouse remain separate, and no synthetic value is used as a claim about Lagos, Abuja, or Cape Town.

The real platform still reports its true state: it has two days of real fast-source history, lacks a fuel-market source, and does not publish its real City Intelligence Score.
