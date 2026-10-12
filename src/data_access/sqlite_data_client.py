"""
SQLite data adapter for the local portfolio demonstration.

Loads synthetic SAP JSON datasets into an in-memory SQLite
database and exposes the StructuredDataClient interface.
"""

import json
import sqlite3
import threading
from pathlib import Path


DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "sap"
)


class SQLiteDataClient:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or DEFAULT_DATA_DIR)
        self._thread_local = threading.local()
        self._connections = []
        self._connections_lock = threading.Lock()

    @property
    def connection(self):
        connection = getattr(
            self._thread_local, "connection", None
        )

        if connection is None:
            connection = sqlite3.connect(":memory:")
            connection.row_factory = sqlite3.Row

            try:
                self._initialize_connection(connection)
            except Exception:
                connection.close()
                raise

            self._thread_local.connection = connection

            with self._connections_lock:
                self._connections.append(connection)

        return connection

    def _initialize_connection(self, connection):
        datasets = (
            "customers",
            "orders",
            "order_items",
            "products",
        )

        for name in datasets:
            path = self.data_dir / f"{name}.json"

            records = json.loads(
                path.read_text(encoding="utf-8")
            )

            if not isinstance(records, list):
                raise ValueError(
                    f"Expected a list in {path}"
                )

            if not records:
                raise ValueError(
                    f"Dataset is empty: {path}"
                )

            columns = list(records[0].keys())

            if not all(
                isinstance(record, dict)
                and set(record.keys()) == set(columns)
                for record in records
            ):
                raise ValueError(
                    f"Inconsistent records in {path}"
                )

            quoted_columns = ", ".join(
                f'"{column}" TEXT'
                for column in columns
            )

            connection.execute(
                f'CREATE TABLE "{name}" ({quoted_columns})'
            )

            column_names = ", ".join(
                f'"{column}"'
                for column in columns
            )

            placeholders = ", ".join(
                "?" for _ in columns
            )

            connection.executemany(
                f'INSERT INTO "{name}" ({column_names}) '
                f'VALUES ({placeholders})',
                [
                    [
                        None if record[column] is None
                        else str(record[column])
                        for column in columns
                    ]
                    for record in records
                ],
            )

        connection.execute(
            "CREATE INDEX idx_orders_id "
            "ON orders(order_id)"
        )

        connection.execute(
            "CREATE INDEX idx_customers_id "
            "ON customers(customer_id)"
        )

        connection.execute(
            "CREATE INDEX idx_items_order "
            "ON order_items(order_id)"
        )

        connection.commit()

    def get_order(self, order_id: str) -> dict:
        order = self.connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        if order is None:
            return {"found": False, "data": None}

        data = dict(order)

        items = self.connection.execute(
            """
            SELECT
                oi.order_item_id,
                oi.product_id,
                p.product_name,
                oi.quantity,
                oi.unit_price,
                oi.total_price,
                oi.currency
            FROM order_items AS oi
            LEFT JOIN products AS p
                ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.order_item_id
            """,
            (order_id,),
        ).fetchall()

        data["items"] = [
            dict(item)
            for item in items
        ]

        return {
            "found": True,
            "data": data,
        }

    def get_customer(self, customer_id: str) -> dict:
        customer = self.connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()

        if customer is None:
            return {"found": False, "data": None}

        return {
            "found": True,
            "data": dict(customer),
        }

    def close(self):
        # Connections are owned by their creating threads.
        # Do not close a connection from another thread.
        connection = getattr(
            self._thread_local, "connection", None
        )

        if connection is not None:
            connection.close()
            self._thread_local.connection = None

            with self._connections_lock:
                self._connections = [
                    item for item in self._connections
                    if item is not connection
                ]
