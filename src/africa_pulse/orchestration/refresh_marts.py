from collections import defaultdict
from datetime import UTC, datetime
from statistics import median
from zoneinfo import ZoneInfo

from africa_pulse.settings import Settings
from africa_pulse.warehouse.client import get_client, insert_rows


def rows(client, query):
    return list(client.query(query).named_results())


def local_date(timestamp, timezone):
    return timestamp.astimezone(ZoneInfo(timezone)).date()


def run():
    client = get_client(Settings.from_environment())
    refreshed_at = datetime.now(UTC)
    cities = {row["city_id"]: row for row in rows(client, "SELECT city_id, timezone, currency_code, country_code FROM warehouse.dim_city FINAL")}
    refresh_mobility(client, cities, refreshed_at)
    refresh_climate(client, cities, refreshed_at)
    refresh_economic(client, cities, refreshed_at)
    refresh_intelligence(client, cities, refreshed_at)


def refresh_mobility(client, cities, refreshed_at):
    grouped = defaultdict(list)
    for row in rows(client, "SELECT city_id, road_sample_id, observed_at, current_speed_kph, free_flow_speed_kph, confidence FROM warehouse.fact_traffic_flow_observation FINAL"):
        grouped[(row["city_id"], local_date(row["observed_at"], cities[row["city_id"]]["timezone"]))].append(row)
    output = []
    sample_totals = {
        row["city_id"]: row["count"]
        for row in rows(client, "SELECT city_id, count() AS count FROM warehouse.dim_road_sample FINAL GROUP BY city_id")
    }
    for (city_id, day), values in grouped.items():
        output.append({
            "city_id": city_id, "local_date": day, "observations": len(values), "valid_observations": len(values),
            "valid_sample_coverage_pct": 100 * len({value["road_sample_id"] for value in values}) / sample_totals[city_id],
            "median_current_speed_kph": median(value["current_speed_kph"] for value in values),
            "median_free_flow_speed_kph": median(value["free_flow_speed_kph"] for value in values),
            "median_congestion_ratio": median(1 - value["current_speed_kph"] / value["free_flow_speed_kph"] for value in values),
            "average_confidence": sum(value["confidence"] for value in values) / len(values),
            "freshest_observation_at": max(value["observed_at"] for value in values), "refreshed_at": refreshed_at,
        })
    insert_rows(client, "mart.city_mobility_daily", output)


def refresh_climate(client, cities, refreshed_at):
    weather = defaultdict(list)
    air = defaultdict(list)
    for row in rows(client, "SELECT city_id, observed_at, temperature_celsius, precipitation_mm, wind_speed_kph FROM warehouse.fact_weather_observation FINAL"):
        weather[(row["city_id"], local_date(row["observed_at"], cities[row["city_id"]]["timezone"]))].append(row)
    for row in rows(client, "SELECT city_id, observed_at, pm2_5_micrograms_per_cubic_metre, pm10_micrograms_per_cubic_metre, nitrogen_dioxide_micrograms_per_cubic_metre FROM warehouse.fact_air_quality_observation FINAL"):
        air[(row["city_id"], local_date(row["observed_at"], cities[row["city_id"]]["timezone"]))].append(row)
    output = []
    for key in weather.keys() | air.keys():
        city_id, day = key
        weather_values, air_values = weather[key], air[key]
        output.append({
            "city_id": city_id, "local_date": day, "weather_observations": len(weather_values), "air_quality_observations": len(air_values),
            "average_temperature_celsius": sum(v["temperature_celsius"] for v in weather_values) / len(weather_values) if weather_values else 0,
            "total_precipitation_mm": sum(v["precipitation_mm"] for v in weather_values),
            "average_wind_speed_kph": sum(v["wind_speed_kph"] for v in weather_values) / len(weather_values) if weather_values else 0,
            "average_pm2_5_micrograms_per_cubic_metre": sum(v["pm2_5_micrograms_per_cubic_metre"] for v in air_values) / len(air_values) if air_values else 0,
            "average_pm10_micrograms_per_cubic_metre": sum(v["pm10_micrograms_per_cubic_metre"] for v in air_values) / len(air_values) if air_values else 0,
            "average_nitrogen_dioxide_micrograms_per_cubic_metre": sum(v["nitrogen_dioxide_micrograms_per_cubic_metre"] for v in air_values) / len(air_values) if air_values else 0,
            "freshest_observation_at": max([v["observed_at"] for v in weather_values + air_values]), "refreshed_at": refreshed_at,
        })
    insert_rows(client, "mart.city_climate_environment_daily", output)


def refresh_economic(client, cities, refreshed_at):
    rates = {
        row["quote_currency"]: row
        for row in rows(
            client,
            "SELECT quote_currency, max(observed_at) AS latest_observed_at, "
            "argMax(rate_quote_per_base, observed_at) AS rate_quote_per_base "
            "FROM warehouse.fact_fx_rate FINAL GROUP BY quote_currency",
        )
    }
    inflation = {
        row["country_code"]: row
        for row in rows(
            client,
            "SELECT country_code, argMax(value, reference_year) AS latest_value, "
            "max(reference_year) AS latest_reference_year "
            "FROM warehouse.fact_economic_indicator_release FINAL "
            "WHERE indicator_code = 'FP.CPI.TOTL.ZG' GROUP BY country_code",
        )
    }
    output = []
    for city_id, city in cities.items():
        rate = rates.get(city["currency_code"])
        if not rate:
            continue
        output.append({"city_id": city_id, "local_date": local_date(rate["latest_observed_at"], city["timezone"]), "currency_code": city["currency_code"], "usd_rate": rate["rate_quote_per_base"], "fx_observation_count": 1, "latest_country_inflation_pct": inflation.get(city["country_code"], {}).get("latest_value"), "latest_country_inflation_year": inflation.get(city["country_code"], {}).get("latest_reference_year"), "freshest_observation_at": rate["latest_observed_at"], "refreshed_at": refreshed_at})
    insert_rows(client, "mart.city_economic_daily", output)


def refresh_intelligence(client, cities, refreshed_at):
    mobility = {(r["city_id"], r["local_date"]): r for r in rows(client, "SELECT * FROM mart.city_mobility_daily FINAL")}
    climate = {(r["city_id"], r["local_date"]): r for r in rows(client, "SELECT * FROM mart.city_climate_environment_daily FINAL")}
    output = []
    for key in mobility.keys() | climate.keys():
        city_id, day = key
        mobility_row, climate_row = mobility.get(key), climate.get(key)
        mobility_component = 100 * (1 - mobility_row["median_congestion_ratio"]) if mobility_row else None
        environment_component = max(0, 100 - 2 * climate_row["average_pm2_5_micrograms_per_cubic_metre"]) if climate_row else None
        coverage = (30 if mobility_component is not None else 0) + (20 if environment_component is not None else 0)
        output.append({"city_id": city_id, "local_date": day, "mobility_component": mobility_component, "commercial_component": None, "environment_component": environment_component, "market_component": None, "direction_component": None, "weighted_coverage_pct": coverage, "score_confidence_pct": coverage, "score_status": "unavailable", "city_intelligence_score": None, "formula_version": "v1_provisional", "limitation": "Commercial density needs approved boundaries; market stability needs a seven-day FX window; direction needs a 28-day history.", "refreshed_at": refreshed_at})
    insert_rows(client, "mart.city_intelligence_daily", output)


if __name__ == "__main__":
    run()
