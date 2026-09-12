from collections.abc import Iterable
from typing import Any

import clickhouse_connect

from africa_pulse.settings import Settings


def get_client(settings: Settings):
    """Create the only ClickHouse connection used by ingestion commands."""
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_username,
        password=settings.clickhouse_password,
    )


def insert_rows(client: Any, table: str, rows: Iterable[dict[str, Any]]) -> int:
    """Insert dictionary rows while making an empty batch an explicit no-op."""
    materialized = list(rows)
    if not materialized:
        return 0
    columns = list(materialized[0])
    values = [[row[column] for column in columns] for row in materialized]
    client.insert(table, values, column_names=columns)
    return len(materialized)
