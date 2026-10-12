"""V6.1.9 — SQLite JSON cache correctness tests."""

import json
import threading

import pytest

from src.data_access.sqlite_data_client import (
    SQLiteDataClient,
    _load_cached_records,
    _read_dataset,
)


def test_cached_dataset_returns_independent_objects(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text(
        json.dumps([{"id": "1", "name": "Original"}]),
        encoding="utf-8",
    )

    first = _read_dataset(path)
    first[0]["name"] = "Modified"

    second = _read_dataset(path)

    assert second[0]["name"] == "Original"
    assert first is not second
    assert first[0] is not second[0]


def test_cache_reloads_after_file_change(tmp_path):
    path = tmp_path / "sample.json"

    path.write_text(
        json.dumps([{"id": "1", "name": "Alpha"}]),
        encoding="utf-8",
    )

    first = _read_dataset(path)
    assert first[0]["name"] == "Alpha"

    # Different file size guarantees a changed cache key.
    path.write_text(
        json.dumps([{"id": "1", "name": "Beta updated"}]),
        encoding="utf-8",
    )

    second = _read_dataset(path)

    assert second[0]["name"] == "Beta updated"


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        "[]",
        '[1, 2, 3]',
        "not valid json",
    ],
)
def test_invalid_json_is_rejected(tmp_path, payload):
    path = tmp_path / "invalid.json"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises((ValueError, json.JSONDecodeError)):
        _read_dataset(path)


def test_sqlite_clients_have_independent_connections():
    first = SQLiteDataClient()
    second = SQLiteDataClient()

    try:
        connection_a = first.connection
        connection_b = second.connection

        assert connection_a is not connection_b

        connection_a.execute(
            "CREATE TABLE cache_isolation_test (value TEXT)"
        )
        connection_a.execute(
            "INSERT INTO cache_isolation_test VALUES (?)",
            ("only_first",),
        )

        exists_in_second = connection_b.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' "
            "AND name = 'cache_isolation_test'"
        ).fetchone()

        assert exists_in_second is None

    finally:
        first.close()
        second.close()


def test_sqlite_client_connections_are_thread_local():
    client = SQLiteDataClient()
    main_connection = client.connection

    worker_connections = []
    worker_errors = []

    def worker():
        try:
            worker_connection = client.connection
            worker_connections.append(worker_connection)

            result = worker_connection.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()

            assert result[0] > 0

        except Exception as exc:
            worker_errors.append(exc)

        finally:
            client.close()

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=10)

    try:
        assert not thread.is_alive()
        assert not worker_errors
        assert len(worker_connections) == 1
        assert worker_connections[0] is not main_connection

        result = main_connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()

        assert result[0] > 0

    finally:
        client.close()
