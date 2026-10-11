from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CsvInfo:
    path: Path
    rows: int
    columns: tuple[str, ...]
    first_time: str
    last_time: str


def _time_value(
    row: dict[str, str],
) -> str:
    lowered = {
        str(key).lower(): value
        for key, value in row.items()
    }

    for key in (
        "time",
        "timestamp",
        "datetime",
        "date",
    ):
        value = lowered.get(key)

        if value:
            return str(value)

    return "?"


def inspect_csv(
    path: Path,
) -> CsvInfo:
    rows = 0
    first_time = "?"
    last_time = "?"
    columns: tuple[str, ...] = ()

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle
        )

        columns = tuple(
            reader.fieldnames
            or ()
        )

        for row in reader:
            rows += 1
            value = _time_value(
                row
            )

            if rows == 1:
                first_time = value

            last_time = value

    return CsvInfo(
        path=path,
        rows=rows,
        columns=columns,
        first_time=first_time,
        last_time=last_time,
    )


def discover(
    roots: Iterable[Path] | None = None,
) -> list[CsvInfo]:
    selected_roots = list(
        roots
        or [
            PROJECT_ROOT / "data",
        ]
    )

    csv_files: list[Path] = []

    for root in selected_roots:
        if root.exists():
            csv_files.extend(
                root.rglob("*.csv")
            )

    results: list[CsvInfo] = []

    for path in sorted(
        set(csv_files)
    ):
        try:
            results.append(
                inspect_csv(path)
            )

        except Exception as error:
            results.append(
                CsvInfo(
                    path=path,
                    rows=-1,
                    columns=(
                        (
                            "ERROR:"
                            f"{type(error).__name__}:"
                            f"{error}"
                        ),
                    ),
                    first_time="?",
                    last_time="?",
                )
            )

    return results
