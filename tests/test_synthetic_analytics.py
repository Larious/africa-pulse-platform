import pytest

from africa_pulse.synthetic_analytics import analyze, score
from africa_pulse.synthetic_demo import scenario_rows


def test_missing_inputs_suppress_score_without_reweighting():
    result = score({'mobility': 80, 'commercial': 60, 'environment': None, 'market': 90, 'direction': None})
    assert result == {'score': None, 'coverage_pct': 65, 'status': 'unavailable'}


def test_score_contributions_and_trends_are_derived():
    rows = scenario_rows()
    results = analyze(rows)
    assert len(results) == 3
    for result in results:
        assert result['score'] == pytest.approx(sum(result['contributions'].values()))
        assert result['coverage_pct'] == 100
    # Reverse the data values across dates to reverse the measured trend.
    lagos = [dict(r) for r in rows if r['city_id'] == 'lagos_ng']
    original = analyze(lagos)[0]['congestion_change_pp']
    congestion = [r['congestion_ratio'] for r in lagos][::-1]
    for row, value in zip(lagos, congestion):
        row['congestion_ratio'] = value
    assert analyze(lagos)[0]['congestion_change_pp'] == pytest.approx(-original)


def test_short_history_is_not_eligible():
    result = analyze(scenario_rows(days=6))[0]
    assert result['score'] is None
    assert result['trend'] == 'insufficient_history'
