from africa_pulse.synthetic_demo import CITIES, SCENARIO_ID, SEED, scenario_rows


def test_synthetic_scenario_has_a_complete_35_day_city_series():
    rows = scenario_rows()

    assert len(rows) == 35 * len(CITIES)
    assert {row["scenario_id"] for row in rows} == {SCENARIO_ID}
    assert {row["seed"] for row in rows} == {SEED}
    assert {row["city_id"] for row in rows} == set(CITIES)
    assert all(0 <= row["congestion_ratio"] <= 1 for row in rows)
    assert all(row["fuel_usd_per_litre"] > 0 for row in rows)
    assert all(row["commercial_services_per_100k"] > 0 for row in rows)
    assert all(0 <= row["city_intelligence_score"] <= 100 for row in rows)
