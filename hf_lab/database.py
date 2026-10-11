from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATABASE = (
    PROJECT_ROOT
    / "hf_lab"
    / "database"
    / "hf_lab.sqlite3"
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


@contextmanager
def connect(
    path: str | Path = DEFAULT_DATABASE,
) -> Iterator[sqlite3.Connection]:
    database = Path(path)

    database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        database,
        timeout=30.0,
    )

    connection.row_factory = sqlite3.Row

    try:
        connection.execute(
            "PRAGMA journal_mode=WAL"
        )

        connection.execute(
            "PRAGMA foreign_keys=ON"
        )

        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize(
    path: str | Path = DEFAULT_DATABASE,
) -> None:
    with connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                finished_at TEXT,
                mode TEXT NOT NULL,
                dataset TEXT NOT NULL,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                side TEXT NOT NULL,
                signal_time TEXT NOT NULL,
                confidence REAL NOT NULL,
                accepted INTEGER NOT NULL,
                rejection_reason TEXT,
                features_json TEXT NOT NULL DEFAULT '{}',

                FOREIGN KEY(run_id)
                REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                signal_id INTEGER,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,

                side TEXT NOT NULL
                CHECK(side IN ('BUY', 'SELL')),

                signal_time TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,

                entry_price REAL NOT NULL,
                exit_price REAL,

                stop_price REAL NOT NULL,
                target_price REAL NOT NULL,

                gross_r REAL,
                fee_r REAL NOT NULL DEFAULT 0,
                slippage_r REAL NOT NULL DEFAULT 0,
                net_r REAL,

                result TEXT NOT NULL DEFAULT 'OPEN',

                metadata_json TEXT NOT NULL DEFAULT '{}',

                FOREIGN KEY(run_id)
                REFERENCES runs(id),

                FOREIGN KEY(signal_id)
                REFERENCES signals(id)
            );

            CREATE INDEX IF NOT EXISTS idx_hf_signals_run
            ON signals(run_id, symbol, signal_time);

            CREATE INDEX IF NOT EXISTS idx_hf_trades_run
            ON trades(run_id, result);

            CREATE INDEX IF NOT EXISTS idx_hf_trades_time
            ON trades(symbol, signal_time);

            CREATE TABLE IF NOT EXISTS daily_metrics (
                run_id INTEGER NOT NULL,
                day TEXT NOT NULL,

                trades INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,

                win_rate REAL NOT NULL,
                net_r REAL NOT NULL,
                average_r REAL NOT NULL,
                profit_factor REAL NOT NULL,
                max_drawdown_r REAL NOT NULL,

                PRIMARY KEY(run_id, day),

                FOREIGN KEY(run_id)
                REFERENCES runs(id)
            );
            """
        )


def create_run(
    *,
    mode: str,
    dataset: str,
    config: dict[str, Any],
    path: str | Path = DEFAULT_DATABASE,
) -> int:
    initialize(path)

    with connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO runs(
                created_at,
                mode,
                dataset,
                status,
                config_json
            )
            VALUES (?, ?, ?, 'RUNNING', ?)
            """,
            (
                utc_now(),
                mode,
                dataset,
                json.dumps(
                    config,
                    sort_keys=True,
                ),
            ),
        )

        return int(
            cursor.lastrowid
        )


def integrity(
    path: str | Path = DEFAULT_DATABASE,
) -> str:
    initialize(path)

    with connect(path) as connection:
        result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

    return str(result)
