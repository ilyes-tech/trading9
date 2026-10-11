from __future__ import annotations

from pathlib import Path
import tempfile

from hf_lab.config import CONFIG
from hf_lab.database import (
    create_run,
    integrity,
)
from hf_lab.inventory import discover
from hf_lab.metrics import calculate


def main() -> None:
    CONFIG.validate()

    assert CONFIG.shadow_only is True
    assert CONFIG.allow_real_orders is False

    assert (
        CONFIG.allow_private_exchange_api
        is False
    )

    sample_metrics = calculate(
        [
            0.40,
            0.40,
            -1.00,
            0.40,
        ]
    )

    assert sample_metrics.trades == 4
    assert sample_metrics.wins == 3

    assert abs(
        sample_metrics.win_rate
        - 0.75
    ) < 1e-12

    assert abs(
        sample_metrics.net_r
        - 0.20
    ) < 1e-12

    with tempfile.TemporaryDirectory() as folder:
        database = (
            Path(folder)
            / "hf_lab_smoke.sqlite3"
        )

        run_id = create_run(
            mode="SMOKE",
            dataset="synthetic",
            config=CONFIG.to_dict(),
            path=database,
        )

        assert run_id == 1
        assert integrity(database) == "ok"

    files = discover()

    print(
        "HF_LAB_VERSION="
        + CONFIG.version
    )

    print("CONFIG=OK")
    print("SAFETY_SHADOW_ONLY=OK")
    print("REAL_ORDERS_LOCKED=OK")
    print("PRIVATE_API_LOCKED=OK")
    print("METRICS_ENGINE=OK")
    print("SQLITE_ENGINE=OK")

    print(
        f"CSV_DISCOVERED={len(files)}"
    )

    print("SMOKE_TEST=OK")


if __name__ == "__main__":
    main()
