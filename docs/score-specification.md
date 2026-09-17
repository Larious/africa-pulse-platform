# City Intelligence Score Specification

Version `v1_provisional` defines five weighted components: mobility 30%, commercial intensity 20%, environment 20%, market stability 15%, and direction of change 15%.

The platform currently publishes `unavailable`, not an invented score. The live platform has only an initial observation window; commercial density has no approved boundary/population denominator; market stability needs at least seven days of FX observations; and direction of change needs 28 days. Individual available components remain visible.

When all component rules are met, a score is the weighted sum of 0-100 components, and a full score requires at least 80% weighted coverage with no required source stale beyond its SLA. Score confidence is separate from the score and reflects coverage, freshness, and quality.

The score must remain unavailable until the approval and history gates are satisfied. Do not backfill invented values or treat the existing candidate-area counts as commercial density.
