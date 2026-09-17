# Analytical Deliverables

`analytics/business_questions.sql` contains the five implemented cross-domain consumer questions. It deliberately uses mart joins rather than hard-coded answers. Run `analytics/question_readiness.sql` first to determine whether the available evidence supports an answer.

1. Executive comparison joins mobility, environment, economic context, and score coverage.
2. Mobility and weather compares congestion with local-day rainfall and temperature.
3. Environmental pressure compares PM2.5 and nitrogen dioxide with congestion.
4. Economic context shows currency rates and country inflation context.
5. Uncertainty reports score coverage, missing components, and evidence availability.

Current records only support an initial cross-sectional comparison. Trend conclusions must wait for scheduled historical observations. This limitation is surfaced by freshness and score coverage fields rather than hidden in a chart.

The project brief's additional fuel-economics and commercial-services-per-population questions require governed source additions before they can be answered. See `docs/question-coverage-plan.md`; the platform must return `not_ready` rather than imply these questions have been answered.
