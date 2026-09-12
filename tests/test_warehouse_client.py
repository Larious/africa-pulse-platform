from africa_pulse.warehouse.client import insert_rows


class RecordingClient:
    def __init__(self):
        self.table = None
        self.values = None
        self.columns = None

    def insert(self, table, values, column_names):
        self.table = table
        self.values = values
        self.columns = column_names


def test_insert_rows_converts_named_records_to_clickhouse_row_order():
    client = RecordingClient()
    count = insert_rows(client, "warehouse.example", [{"city_id": "lagos_ng", "speed": 42}])
    assert count == 1
    assert client.table == "warehouse.example"
    assert client.columns == ["city_id", "speed"]
    assert client.values == [["lagos_ng", 42]]


def test_insert_rows_skips_empty_batches():
    client = RecordingClient()
    assert insert_rows(client, "warehouse.example", []) == 0
    assert client.table is None
