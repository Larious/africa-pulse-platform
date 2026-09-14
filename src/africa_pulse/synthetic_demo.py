"""Clearly labelled synthetic scenario for demonstrating missing analytical capabilities."""

import argparse
import json
import random
from datetime import UTC, date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from africa_pulse.settings import Settings
from africa_pulse.warehouse.client import get_client, insert_rows

SCENARIO_ID = "synthetic_capstone_demo_v1"
SEED = 20260914
SCHEMA = """
CREATE DATABASE IF NOT EXISTS synthetic_demo;
CREATE TABLE IF NOT EXISTS synthetic_demo.city_daily_scenario
(
    scenario_id LowCardinality(String), seed UInt64, city_id LowCardinality(String), city_name String,
    local_date Date, congestion_ratio Float32, rainfall_mm Float32, pm2_5 Float32,
    nitrogen_dioxide Float32, usd_rate Float64, fuel_local_per_litre Float64,
    fuel_usd_per_litre Float64, population UInt64, commercial_services UInt32,
    commercial_services_per_100k Float32, city_intelligence_score Float32,
    trend_status LowCardinality(String), generated_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(generated_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (scenario_id, city_id, local_date);
"""

CITIES = {
    "lagos_ng": {"name": "Lagos", "population": 15500000, "usd_rate": 1550.0, "fuel": 940.0, "congestion": 0.48, "rain": 8.0, "pm": 29.0, "no2": 31.0, "services": 32500, "trend": -0.002},
    "abuja_ng": {"name": "Abuja", "population": 4100000, "usd_rate": 1550.0, "fuel": 920.0, "congestion": 0.33, "rain": 5.5, "pm": 20.0, "no2": 18.0, "services": 10800, "trend": -0.001},
    "cape_town_za": {"name": "Cape Town", "population": 4800000, "usd_rate": 18.2, "fuel": 24.0, "congestion": 0.27, "rain": 3.0, "pm": 15.0, "no2": 14.0, "services": 17100, "trend": 0.0005},
}


def create_schema(client) -> None:
    for statement in SCHEMA.split(";"):
        if statement.strip():
            client.command(statement)


def scenario_rows(start_date: date = date(2026, 8, 11), days: int = 35) -> list[dict]:
    """Return a repeatable illustrative scenario; these are not source observations."""
    generator = random.Random(SEED)
    generated_at = datetime.now(UTC)
    rows = []
    for city_id, baseline in CITIES.items():
        services_per_100k = baseline["services"] / baseline["population"] * 100000
        for day_index in range(days):
            local_date = start_date + timedelta(days=day_index)
            rainfall = max(0, baseline["rain"] + generator.gauss(0, 2.3))
            congestion = min(0.9, max(0.05, baseline["congestion"] + baseline["trend"] * day_index + rainfall * 0.004 + generator.gauss(0, 0.018)))
            pm2_5 = max(3, baseline["pm"] + congestion * 9 + generator.gauss(0, 2.0))
            no2 = max(2, baseline["no2"] + congestion * 7 + generator.gauss(0, 1.5))
            usd_rate = baseline["usd_rate"] * (1 + 0.0008 * day_index + generator.gauss(0, 0.003))
            fuel_local = baseline["fuel"] * (1 + 0.0015 * day_index + generator.gauss(0, 0.006))
            fuel_usd = fuel_local / usd_rate
            score = max(0, min(100, 100 - congestion * 55 - pm2_5 * 0.8 + services_per_100k * 0.06 - fuel_usd * 2))
            trend_status = "improving" if baseline["trend"] < 0 else "deteriorating"
            rows.append({
                "scenario_id": SCENARIO_ID, "seed": SEED, "city_id": city_id, "city_name": baseline["name"],
                "local_date": local_date, "congestion_ratio": congestion, "rainfall_mm": rainfall, "pm2_5": pm2_5,
                "nitrogen_dioxide": no2, "usd_rate": usd_rate, "fuel_local_per_litre": fuel_local,
                "fuel_usd_per_litre": fuel_usd, "population": baseline["population"], "commercial_services": baseline["services"],
                "commercial_services_per_100k": services_per_100k, "city_intelligence_score": score,
                "trend_status": trend_status, "generated_at": generated_at,
            })
    return rows


def generate(client) -> int:
    create_schema(client)
    count = insert_rows(client, "synthetic_demo.city_daily_scenario", scenario_rows())
    from africa_pulse.synthetic_analytics import install
    install(client, SCENARIO_ID)
    return count


def query_rows(client, sql: str, parameters: dict | None = None) -> list[dict]:
    return list(client.query(sql, parameters=parameters).named_results())


def summary(client) -> dict:
    from africa_pulse.synthetic_analytics import summary as analytical_summary
    return analytical_summary(client, SCENARIO_ID)


from pathlib import Path

PAGE = Path(__file__).with_name("synthetic_dashboard.html").read_text()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.respond(200, "text/html; charset=utf-8", PAGE.encode())
        elif self.path == "/api/summary":
            self.respond(200, "application/json", json.dumps(summary(self.server.client), default=str).encode())
        else:
            self.respond(404, "text/plain; charset=utf-8", b"Not found")

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def run_dashboard(port: int = 8766) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.client = get_client(Settings.from_environment())
    print(f"Synthetic dashboard: http://127.0.0.1:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isolated Africa Pulse synthetic demonstration.")
    parser.add_argument("--generate", action="store_true", help="Generate the deterministic synthetic scenario.")
    parser.add_argument("--dashboard", action="store_true", help="Serve the synthetic dashboard on port 8766.")
    args = parser.parse_args()
    client = get_client(Settings.from_environment())
    if args.generate:
        print(f"Inserted {generate(client)} synthetic scenario rows into synthetic_demo.")
    if args.dashboard:
        run_dashboard()
    if not args.generate and not args.dashboard:
        parser.error("choose --generate, --dashboard, or both")


if __name__ == "__main__":
    main()
