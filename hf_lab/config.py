from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HFLabConfig:
    project_name: str = "TradingAI HF Lab 400"
    version: str = "0.1.0"

    # Objectifs de recherche, pas des garanties.
    target_trades_per_day: int = 400
    target_win_rate: float = 0.80

    # Verrous absolus de sécurité.
    shadow_only: bool = True
    allow_real_orders: bool = False
    allow_private_exchange_api: bool = False

    # Coûts provisoires à calibrer plus tard.
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 1.0
    simulated_latency_ms: int = 250

    # Séparation chronologique anti-surapprentissage.
    train_ratio: float = 0.60
    validation_ratio: float = 0.20
    test_ratio: float = 0.20

    first_review_trades: int = 1_000
    strong_review_trades: int = 5_000
    final_review_trades: int = 10_000

    maximum_trades_per_day_safety: int = 600
    maximum_open_trades: int = 20

    def validate(self) -> None:
        if not self.shadow_only:
            raise ValueError(
                "HF Lab doit rester en mode SHADOW."
            )

        if self.allow_real_orders:
            raise ValueError(
                "Les ordres réels sont interdits."
            )

        if self.allow_private_exchange_api:
            raise ValueError(
                "Les API privées sont interdites."
            )

        if self.target_trades_per_day <= 0:
            raise ValueError(
                "La cible quotidienne doit être positive."
            )

        if not 0.0 < self.target_win_rate < 1.0:
            raise ValueError(
                "Le win rate cible doit être compris entre 0 et 1."
            )

        split = (
            self.train_ratio
            + self.validation_ratio
            + self.test_ratio
        )

        if abs(split - 1.0) > 1e-9:
            raise ValueError(
                "Train + validation + test doivent totaliser 1."
            )

        if (
            self.maximum_trades_per_day_safety
            < self.target_trades_per_day
        ):
            raise ValueError(
                "La limite de sécurité est inférieure à la cible."
            )

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return asdict(self)


CONFIG = HFLabConfig()
CONFIG.validate()
