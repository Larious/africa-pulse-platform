"""Derived synthetic analytics; never queries the real warehouse or marts."""
from collections import defaultdict
from statistics import mean, pstdev

WEIGHTS = {'mobility': .30, 'commercial': .20, 'environment': .20, 'market': .15, 'direction': .15}
BASE = 'synthetic_demo.city_daily_scenario FINAL'
VIEWS = {
    'mobility': 'scenario_id, city_id, city_name, local_date, congestion_ratio, toUInt32(round(100000 * (1 - congestion_ratio) * if(toDayOfWeek(local_date) > 5, 0.75, 1))) AS trips',
    'environment': 'scenario_id, city_id, local_date, rainfall_mm, pm2_5, nitrogen_dioxide',
    'market': 'scenario_id, city_id, local_date, usd_rate, fuel_local_per_litre',
    'commercial': 'scenario_id, city_id, local_date, population, commercial_services',
}
QUERIES = {
    'Mobility and commercial provision': 'SELECT m.city_name, avg(m.trips) AS daily_trips, avg(c.commercial_services / c.population * 100000) AS services_per_100k FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.commercial c USING (scenario_id, city_id, local_date) GROUP BY m.city_name',
    'Rainfall and mobility': 'SELECT m.city_name, count() AS paired_days, corr(e.rainfall_mm, m.congestion_ratio) AS correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) GROUP BY m.city_name',
    'Air pressure and mobility': 'SELECT m.city_name, avg(e.pm2_5) AS pm2_5, avg(e.nitrogen_dioxide) AS no2, corr(e.pm2_5, m.congestion_ratio) AS correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) GROUP BY m.city_name',
    'Fuel costs and transport activity': 'SELECT m.city_name, avg(k.fuel_local_per_litre / k.usd_rate * 8) AS fuel_usd_per_100km, corr(k.fuel_local_per_litre / k.usd_rate, m.trips) AS fuel_trip_correlation FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.market k USING (scenario_id, city_id, local_date) GROUP BY m.city_name',
    'Service provision and air quality': 'SELECT m.city_name, avg(c.commercial_services / c.population * 100000) AS services_per_100k, avg(e.pm2_5) AS pm2_5 FROM synthetic_demo.commercial c INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date) INNER JOIN synthetic_demo.mobility m USING (scenario_id, city_id, local_date) GROUP BY m.city_name',
}


def install(client, scenario_id):
    # Source scenario is an internal constant; no user input is interpolated.
    for domain, columns in VIEWS.items():
        client.command(f"CREATE OR REPLACE VIEW synthetic_demo.{domain} AS SELECT {columns} FROM {BASE} WHERE scenario_id = '{scenario_id}'")


def clamp(value):
    return max(0, min(100, value))


def score(components):
    coverage = sum(WEIGHTS[k] for k, v in components.items() if v is not None)
    # Full demonstration score requires all five components; never silently reweight.
    value = sum(WEIGHTS[k] * v for k, v in components.items()) if all(v is not None for v in components.values()) else None
    return {'score': value, 'coverage_pct': round(coverage * 100), 'status': 'eligible' if value is not None else 'unavailable'}


def analyze(records):
    groups = defaultdict(list)
    for row in records:
        groups[row['city_id']].append(row)
    output = []
    for values in groups.values():
        values.sort(key=lambda r: r['local_date'])
        first, last = values[:7], values[-7:]
        change = mean(r['congestion_ratio'] for r in last) - mean(r['congestion_ratio'] for r in first)
        rates = [r['usd_rate'] for r in last]
        components = {
            'mobility': 100 * (1 - mean(r['congestion_ratio'] for r in last)),
            'commercial': clamp(values[-1]['commercial_services'] / values[-1]['population'] * 100000 / 400 * 100),
            'environment': clamp(100 - 2 * mean(r['pm2_5'] for r in last)),
            'market': clamp(100 - 1000 * pstdev(rates) / mean(rates)) if len(values) >= 7 else None,
            'direction': clamp(50 - 500 * change) if len(values) >= 28 else None,
        }
        stress = components | {'environment': None, 'direction': None}
        output.append({'city': values[-1]['city_name'], 'days': len(values),
                       'congestion_change_pp': change * 100,
                       'trend': ('improving' if change < -.01 else 'deteriorating' if change > .01 else 'stable') if len(values) >= 28 else 'insufficient_history',
                       'fx_change_pct': (values[-1]['usd_rate'] / values[0]['usd_rate'] - 1) * 100,
                       'fuel_local_change_pct': (values[-1]['fuel_local_per_litre'] / values[0]['fuel_local_per_litre'] - 1) * 100,
                       'components': components, 'contributions': {k: None if v is None else v * WEIGHTS[k] for k, v in components.items()},
                       **score(components), 'missing_air_and_trend': score(stress), 'series': values})
    return sorted(output, key=lambda row: row['score'] if row['score'] is not None else -1, reverse=True)


def summary(client, scenario_id):
    query = '''SELECT m.city_id AS city_id, m.city_name AS city_name, m.local_date AS local_date, m.congestion_ratio AS congestion_ratio, m.trips AS trips, e.rainfall_mm AS rainfall_mm, e.pm2_5 AS pm2_5, e.nitrogen_dioxide AS nitrogen_dioxide,
    k.usd_rate, k.fuel_local_per_litre, c.population, c.commercial_services
    FROM synthetic_demo.mobility m INNER JOIN synthetic_demo.environment e USING (scenario_id, city_id, local_date)
    INNER JOIN synthetic_demo.market k USING (scenario_id, city_id, local_date)
    INNER JOIN synthetic_demo.commercial c USING (scenario_id, city_id, local_date)'''
    records = list(client.query(query).named_results())
    return {'label': 'SYNTHETIC DEMONSTRATION ONLY', 'scenario_id': scenario_id, 'weights': WEIGHTS,
            'cities': analyze(records), 'questions': {name: list(client.query(sql).named_results()) for name, sql in QUERIES.items()}}
