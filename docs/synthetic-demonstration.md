# Synthetic analytical demonstration

Instructor permission was communicated by the user after a Teams meeting. This scenario is entirely synthetic, including population, fuel, service counts and trip demand. It makes no claims about actual cities. Production `warehouse` and `mart` are not queried or modified.

## Run from VS Code's integrated terminal

```bash
.venv/bin/python -m africa_pulse.synthetic_demo --generate
.venv/bin/python -m africa_pulse.synthetic_demo --dashboard
```

Open http://127.0.0.1:8766. If the installed local launchd service already runs the dashboard, do not launch a second server. Restart it after editing code with:

```bash
launchctl kickstart -k gui/$(id -u)/com.africa-pulse.synthetic-dashboard
```

Docker and ClickHouse must be running. The launchd service is specific to this Mac; the Python commands work in a fresh clone.

## Reproducibility and grain

Seed 20260914 produces 105 daily records, three cities × 35 days, from 11 August through 14 September 2026. Regeneration replaces logical scenario/city/day records when read with FINAL. Generated timestamps vary; simulated values do not. The synthetic daily table retains legacy prototype score/trend fields for compatibility, but the analytical dashboard ignores those fields and calculates results from the underlying measures.

Four domain views (`synthetic_demo.mobility`, `environment`, `market`, `commercial`) project this seeded table. They are not independent source integrations. Five executable joins are provided in `analytics/synthetic_business_questions.sql`. The dashboard executes those queries and shows their results.

## Deliverable map

| Deliverable | Dashboard evidence |
|---|---|
| Executive comparison | Major latest indicators, score, and calculated congestion change/trend |
| Mobility | Daily simulated trips and congestion charts; rainfall correlation with paired-day count |
| Environment | Rainfall, PM2.5 and NO2 charts; cross-city air/mobility analysis |
| Economic | FX and fuel charts, first-to-last changes, local/USD fuel and fuel-only cost per 100 km |
| City Intelligence | Five component contributions, weights, total and coverage |
| Five cross-domain questions | Five actual SQL joins between synthetic domain views |
| Uncertainty | Remove air and direction components: coverage falls to 65% and score becomes unavailable; population-denominator sensitivity is stated |

## Formula v2_demo

Latest seven days are used for mobility, environment and FX stability. All components are clipped to 0–100. The final score sums the following components multiplied by their weights:

- Mobility (30%): 100 × (1 − mean congestion).
- Commercial (20%): services per 100,000 / 400 × 100.
- Environment (20%): 100 − 2 × mean PM2.5.
- Market (15%): 100 − 1000 × seven-day population standard deviation of FX / mean FX.
- Direction (15%): 50 − 500 × (final-seven-day mean congestion − first-seven-day mean congestion).

The five-component weights match the project specification. Normalization constants are provisional demonstration choices; they are not externally validated scientific thresholds. The demonstration requires every component, seven FX days and 28 trend days (stricter than the minimum 80% coverage specification). Missing components suppress the score rather than reweight remaining components.

Trend is calculated from the records: change below −1 percentage point means improving, above +1 means deteriorating, otherwise stable. This is congestion direction only, not a claim about whole-city development. Changes are descriptive, not statistically significant findings.

Trips = rounded 100,000 × (1 − congestion), multiplied by 0.75 at weekends. This is a constructed demand series, not TomTom vehicle counts. Rainfall and pollution relationships are deliberately embedded in the generator, so correlations illustrate calculation rather than discover causal effects.

USD/litre = fuel price in local currency / local currency per USD. Fuel-only USD/100 km assumes 8 litres/100 km and excludes wages, maintenance, fares and other transport costs. Service density compares city-level provision; without district data it cannot identify within-city concentrations.

## Defense

Show the executive table, select a city to trace daily measurements, then show the five join results and score decomposition. Finally show the missing-component experiment. Explain that synthetic permission lets the team demonstrate analytical logic; it does not validate real-world conclusions or complete real-source acquisition.

Validation includes live execution of all five queries, three 35-day series, score-contribution equality, reversed-data trend reversal, short-history suppression, missing-component suppression, and dashboard HTTP checks. The production presentation remains a separate real-data briefing; use this dashboard as the synthetic analytical demonstration.
