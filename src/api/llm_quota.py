"""Persistent daily quota for optional LLM calls."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class DailyLLMQuota:
    def __init__(self, db_path, max_calls=100):
        if max_calls < 0:
            raise ValueError("max_calls must be non-negative")

        self.db_path = str(db_path)
        self.max_calls = max_calls

        Path(self.db_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(
            self.db_path,
            timeout=10,
        ) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS llm_daily_quota (
                    day TEXT PRIMARY KEY,
                    used INTEGER NOT NULL
                )
            """)

    def try_reserve(self):
        """Atomically reserve one call for the current UTC day."""
        day = datetime.now(timezone.utc).date().isoformat()

        with sqlite3.connect(
            self.db_path,
            timeout=10,
        ) as connection:
            cursor = connection.execute(
                """
                INSERT INTO llm_daily_quota (day, used)
                VALUES (?, 1)
                ON CONFLICT(day) DO UPDATE
                    SET used = used + 1
                WHERE used < ?
                RETURNING used
                """,
                (day, self.max_calls),
            )

            reserved = cursor.fetchone() is not None

            if reserved and self.max_calls == 0:
                connection.rollback()
                return False

            return reserved
