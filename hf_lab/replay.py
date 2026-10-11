"""Moteur chronologique de replay historique pour TradingAI HF Lab.

Garanties principales :

- aucune donnée future transmise à la stratégie ;
- signal produit après la clôture d'une bougie ;
- entrée seulement à l'ouverture de la bougie suivante ;
- SL prioritaire lorsque SL et TP sont touchés dans la même bougie ;
- frais et slippage appliqués ;
- aucun ordre réel ou appel à une API privée.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import math
from typing import Any, Callable, Sequence

from hf_lab.database import (
    DEFAULT_DATABASE,
    connect,
    create_run,
    utc_now,
)
from hf_lab.metrics import Metrics, calculate


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    trades: float = 0.0


@dataclass(frozen=True)
class ReplaySignal:
    strategy: str
    side: str

    # Distances absolues par rapport au prix d'entrée de la
    # bougie suivante.
    stop_distance: float
    target_distance: float

    confidence: float = 0.50
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        side = self.side.upper()

        if side not in {
            "BUY",
            "SELL",
        }:
            raise ValueError(
                f"Direction invalide : {self.side}"
            )

        if not self.strategy.strip():
            raise ValueError(
                "Nom de stratégie vide."
            )

        if (
            not math.isfinite(
                self.stop_distance
            )
            or self.stop_distance <= 0
        ):
            raise ValueError(
                "Distance du SL invalide."
            )

        if (
            not math.isfinite(
                self.target_distance
            )
            or self.target_distance <= 0
        ):
            raise ValueError(
                "Distance du TP invalide."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Confiance hors intervalle 0–1."
            )


@dataclass(frozen=True)
class ReplaySettings:
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 1.0

    maximum_holding_bars: int = 48
    force_close_at_end: bool = True

    conservative_intrabar: bool = True
    enter_next_bar: bool = True

    shadow_only: bool = True
    allow_real_orders: bool = False

    def validate(self) -> None:
        if not self.shadow_only:
            raise ValueError(
                "Le replay doit rester SHADOW."
            )

        if self.allow_real_orders:
            raise ValueError(
                "Les ordres réels sont interdits."
            )

        if not self.enter_next_bar:
            raise ValueError(
                "L'entrée sur la bougie suivante est obligatoire."
            )

        if not self.conservative_intrabar:
            raise ValueError(
                "Le mode intrabar prudent est obligatoire."
            )

        if self.fee_bps_per_side < 0:
            raise ValueError(
                "Frais négatifs interdits."
            )

        if self.slippage_bps_per_side < 0:
            raise ValueError(
                "Slippage négatif interdit."
            )

        if self.maximum_holding_bars <= 0:
            raise ValueError(
                "Durée maximale invalide."
            )


@dataclass(frozen=True)
class TradeResult:
    trade_id: int
    signal_id: int

    symbol: str
    strategy: str
    side: str

    signal_time: datetime
    entry_time: datetime
    exit_time: datetime

    raw_entry_price: float
    entry_price: float

    raw_exit_price: float
    exit_price: float

    stop_price: float
    target_price: float

    result: str

    gross_r: float
    fee_r: float
    slippage_r: float
    net_r: float

    holding_bars: int


@dataclass(frozen=True)
class ReplayReport:
    run_id: int
    dataset: str
    symbol: str

    first_time: datetime
    last_time: datetime

    bars: int
    trades: tuple[TradeResult, ...]
    metrics: Metrics


@dataclass
class _PendingSignal:
    signal: ReplaySignal
    signal_id: int
    signal_time: datetime


@dataclass
class _OpenTrade:
    trade_id: int
    signal_id: int

    symbol: str
    signal: ReplaySignal

    signal_time: datetime
    entry_time: datetime
    entry_index: int

    raw_entry_price: float
    entry_price: float

    stop_price: float
    target_price: float
    risk_distance: float


StrategyFunction = Callable[
    [Sequence[Bar]],
    ReplaySignal | None,
]


def _float_value(
    row: dict[str, str],
    key: str,
    default: float = 0.0,
) -> float:
    raw = row.get(
        key,
        "",
    )

    if raw is None:
        return float(default)

    text = str(raw).strip()

    if not text:
        return float(default)

    return float(text)


def parse_timestamp(
    value: str | int | float,
) -> datetime:
    text = str(value).strip()

    if not text:
        raise ValueError(
            "Timestamp vide."
        )

    try:
        numeric = float(text)

    except ValueError:
        normalized = text.replace(
            "Z",
            "+00:00",
        )

        timestamp = datetime.fromisoformat(
            normalized
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(
            timezone.utc
        )

    return datetime.fromtimestamp(
        numeric,
        tz=timezone.utc,
    )


def load_bars(
    path: str | Path,
) -> list[Bar]:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            source
        )

    rows: list[Bar] = []

    with source.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle
        )

        required = {
            "open",
            "high",
            "low",
            "close",
        }

        columns = set(
            reader.fieldnames
            or ()
        )

        if not required.issubset(
            columns
        ):
            raise ValueError(
                f"Colonnes OHLC manquantes dans {source}"
            )

        if (
            "time" not in columns
            and "datetime" not in columns
        ):
            raise ValueError(
                f"Colonne temporelle absente dans {source}"
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            raw_time = (
                row.get("datetime")
                or row.get("time")
            )

            try:
                timestamp = parse_timestamp(
                    str(raw_time)
                )

                open_price = _float_value(
                    row,
                    "open",
                )

                high_price = _float_value(
                    row,
                    "high",
                )

                low_price = _float_value(
                    row,
                    "low",
                )

                close_price = _float_value(
                    row,
                    "close",
                )

                volume = _float_value(
                    row,
                    "volume",
                    0.0,
                )

                trade_count = _float_value(
                    row,
                    "trades",
                    0.0,
                )

            except Exception as error:
                raise ValueError(
                    f"{source}:{row_number} : {error}"
                ) from error

            prices = [
                open_price,
                high_price,
                low_price,
                close_price,
            ]

            if (
                not all(
                    math.isfinite(price)
                    and price > 0
                    for price in prices
                )
            ):
                raise ValueError(
                    f"{source}:{row_number} : prix invalide"
                )

            if high_price < max(
                open_price,
                close_price,
                low_price,
            ):
                raise ValueError(
                    f"{source}:{row_number} : high incohérent"
                )

            if low_price > min(
                open_price,
                close_price,
                high_price,
            ):
                raise ValueError(
                    f"{source}:{row_number} : low incohérent"
                )

            rows.append(
                Bar(
                    time=timestamp,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                    trades=trade_count,
                )
            )

    # Tri chronologique ; les collisions contradictoires sont refusées.
    # Un doublon strictement identique est sans effet.
    deduplicated: dict[datetime, Bar] = {}
    for bar in rows:
        previous = deduplicated.get(bar.time)
        if previous is not None and previous != bar:
            raise ValueError(
                f"{source} : timestamp dupliqué contradictoire : {bar.time.isoformat()}"
            )
        deduplicated[bar.time] = bar

    bars = [
        deduplicated[timestamp]
        for timestamp in sorted(
            deduplicated
        )
    ]

    if len(bars) < 3:
        raise ValueError(
            f"Historique insuffisant : {len(bars)} bougies"
        )

    return bars


def _entry_execution_price(
    *,
    side: str,
    raw_price: float,
    slippage_bps: float,
) -> float:
    rate = (
        slippage_bps
        / 10_000.0
    )

    if side == "BUY":
        return raw_price * (
            1.0 + rate
        )

    return raw_price * (
        1.0 - rate
    )


def _exit_execution_price(
    *,
    side: str,
    raw_price: float,
    slippage_bps: float,
) -> float:
    rate = (
        slippage_bps
        / 10_000.0
    )

    # Fermer un BUY revient à vendre.
    if side == "BUY":
        return raw_price * (
            1.0 - rate
        )

    # Fermer un SELL revient à acheter.
    return raw_price * (
        1.0 + rate
    )


def _close_trade(
    *,
    trade: _OpenTrade,
    bar: Bar,
    raw_exit_price: float,
    result: str,
    holding_bars: int,
    settings: ReplaySettings,
) -> TradeResult:
    side = trade.signal.side.upper()

    exit_price = _exit_execution_price(
        side=side,
        raw_price=raw_exit_price,
        slippage_bps=(
            settings.slippage_bps_per_side
        ),
    )

    if side == "BUY":
        raw_profit = (
            raw_exit_price
            - trade.raw_entry_price
        )

    else:
        raw_profit = (
            trade.raw_entry_price
            - raw_exit_price
        )

    gross_r = (
        raw_profit
        / trade.risk_distance
    )

    entry_slippage = abs(
        trade.entry_price
        - trade.raw_entry_price
    )

    exit_slippage = abs(
        exit_price
        - raw_exit_price
    )

    slippage_r = (
        entry_slippage
        + exit_slippage
    ) / trade.risk_distance

    fee_rate = (
        settings.fee_bps_per_side
        / 10_000.0
    )

    fee_amount = (
        trade.entry_price
        + exit_price
    ) * fee_rate

    fee_r = (
        fee_amount
        / trade.risk_distance
    )

    net_r = (
        gross_r
        - slippage_r
        - fee_r
    )

    return TradeResult(
        trade_id=trade.trade_id,
        signal_id=trade.signal_id,

        symbol=trade.symbol,
        strategy=trade.signal.strategy,
        side=side,

        signal_time=trade.signal_time,
        entry_time=trade.entry_time,
        exit_time=bar.time,

        raw_entry_price=(
            trade.raw_entry_price
        ),
        entry_price=trade.entry_price,

        raw_exit_price=raw_exit_price,
        exit_price=exit_price,

        stop_price=trade.stop_price,
        target_price=trade.target_price,

        result=result,

        gross_r=float(
            gross_r
        ),
        fee_r=float(
            fee_r
        ),
        slippage_r=float(
            slippage_r
        ),
        net_r=float(
            net_r
        ),

        holding_bars=int(
            holding_bars
        ),
    )


def _trade_exit_on_bar(
    *,
    trade: _OpenTrade,
    bar: Bar,
    bar_index: int,
    settings: ReplaySettings,
) -> tuple[str, float] | None:
    side = trade.signal.side.upper()

    if side == "BUY":
        hit_stop = (
            bar.low
            <= trade.stop_price
        )

        hit_target = (
            bar.high
            >= trade.target_price
        )

    else:
        hit_stop = (
            bar.high
            >= trade.stop_price
        )

        hit_target = (
            bar.low
            <= trade.target_price
        )

    # Lorsque les deux niveaux sont touchés dans la même
    # bougie OHLC, l'ordre réel des mouvements est inconnu.
    # Le replay choisit donc le scénario défavorable.
    if hit_stop:
        return (
            "SL",
            trade.stop_price,
        )

    if hit_target:
        return (
            "TP",
            trade.target_price,
        )

    holding_bars = (
        bar_index
        - trade.entry_index
        + 1
    )

    if (
        holding_bars
        >= settings.maximum_holding_bars
    ):
        return (
            "MAX_HOLD",
            bar.close,
        )

    return None


def run_replay(
    *,
    symbol: str,
    dataset: str,
    bars: Sequence[Bar],
    strategy: StrategyFunction,
    settings: ReplaySettings | None = None,
    database_path: str | Path = DEFAULT_DATABASE,
) -> ReplayReport:
    selected_settings = (
        settings
        or ReplaySettings()
    )

    selected_settings.validate()

    if len(bars) < 3:
        raise ValueError(
            "Au moins trois bougies sont requises."
        )

    normalized_symbol = str(
        symbol
    ).upper().strip()

    if not normalized_symbol:
        raise ValueError(
            "Symbole vide."
        )

    run_id = create_run(
        mode="HISTORICAL_REPLAY",
        dataset=dataset,
        config={
            "symbol": normalized_symbol,
            "settings": asdict(
                selected_settings
            ),
            "engine": "HF_REPLAY_V1",
        },
        path=database_path,
    )

    pending: _PendingSignal | None = None
    open_trade: _OpenTrade | None = None

    from hf_lab.history_view import VisibleHistory

    results: list[TradeResult] = []

    with connect(
        database_path
    ) as connection:
        for bar_index, bar in enumerate(
            bars
        ):
            # Le signal de la bougie précédente est exécuté
            # seulement à l'ouverture de la bougie actuelle.
            if (
                pending is not None
                and open_trade is None
            ):
                signal = pending.signal
                signal.validate()

                side = signal.side.upper()

                raw_entry = float(
                    bar.open
                )

                entry_price = (
                    _entry_execution_price(
                        side=side,
                        raw_price=raw_entry,
                        slippage_bps=(
                            selected_settings
                            .slippage_bps_per_side
                        ),
                    )
                )

                if side == "BUY":
                    stop_price = (
                        raw_entry
                        - signal.stop_distance
                    )

                    target_price = (
                        raw_entry
                        + signal.target_distance
                    )

                else:
                    stop_price = (
                        raw_entry
                        + signal.stop_distance
                    )

                    target_price = (
                        raw_entry
                        - signal.target_distance
                    )

                cursor = connection.execute(
                    """
                    INSERT INTO trades(
                        run_id,
                        signal_id,
                        symbol,
                        strategy,
                        side,
                        signal_time,
                        entry_time,
                        entry_price,
                        stop_price,
                        target_price,
                        result,
                        metadata_json
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, 'OPEN', ?
                    )
                    """,
                    (
                        run_id,
                        pending.signal_id,
                        normalized_symbol,
                        signal.strategy,
                        side,
                        pending.signal_time.isoformat(),
                        bar.time.isoformat(),
                        entry_price,
                        stop_price,
                        target_price,
                        json.dumps(
                            {
                                "raw_entry_price": (
                                    raw_entry
                                ),
                                **signal.metadata,
                            },
                            sort_keys=True,
                        ),
                    ),
                )

                open_trade = _OpenTrade(
                    trade_id=int(
                        cursor.lastrowid
                    ),
                    signal_id=(
                        pending.signal_id
                    ),

                    symbol=normalized_symbol,
                    signal=signal,

                    signal_time=(
                        pending.signal_time
                    ),
                    entry_time=bar.time,
                    entry_index=bar_index,

                    raw_entry_price=raw_entry,
                    entry_price=entry_price,

                    stop_price=stop_price,
                    target_price=target_price,
                    risk_distance=(
                        signal.stop_distance
                    ),
                )

                pending = None

            # La position peut atteindre son SL ou son TP pendant
            # la même bougie que son entrée.
            if open_trade is not None:
                exit_decision = (
                    _trade_exit_on_bar(
                        trade=open_trade,
                        bar=bar,
                        bar_index=bar_index,
                        settings=selected_settings,
                    )
                )

                if exit_decision is not None:
                    (
                        result_name,
                        raw_exit,
                    ) = exit_decision

                    holding_bars = (
                        bar_index
                        - open_trade.entry_index
                        + 1
                    )

                    closed = _close_trade(
                        trade=open_trade,
                        bar=bar,
                        raw_exit_price=(
                            raw_exit
                        ),
                        result=result_name,
                        holding_bars=holding_bars,
                        settings=selected_settings,
                    )

                    connection.execute(
                        """
                        UPDATE trades
                        SET
                            exit_time = ?,
                            exit_price = ?,
                            gross_r = ?,
                            fee_r = ?,
                            slippage_r = ?,
                            net_r = ?,
                            result = ?,
                            metadata_json = ?
                        WHERE id = ?
                        """,
                        (
                            closed.exit_time.isoformat(),
                            closed.exit_price,
                            closed.gross_r,
                            closed.fee_r,
                            closed.slippage_r,
                            closed.net_r,
                            closed.result,
                            json.dumps(
                                {
                                    "raw_entry_price": (
                                        closed.raw_entry_price
                                    ),
                                    "raw_exit_price": (
                                        closed.raw_exit_price
                                    ),
                                    "holding_bars": (
                                        closed.holding_bars
                                    ),
                                },
                                sort_keys=True,
                            ),
                            closed.trade_id,
                        ),
                    )

                    results.append(
                        closed
                    )

                    open_trade = None

            # Ne produit pas de signal sur la dernière bougie,
            # car aucune bougie suivante n'existe pour l'entrée.
            if bar_index >= len(bars) - 1:
                continue

            # Une seule position par exécution de stratégie dans
            # cette première version du moteur.
            if (
                open_trade is not None
                or pending is not None
            ):
                continue

            # Vue légère strictement limitée aux bougies déjà clôturées.
            # Aucun préfixe croissant n'est copié à chaque minute.
            visible_history = VisibleHistory(
                bars,
                bar_index + 1,
            )

            signal = strategy(
                visible_history
            )

            if signal is None:
                continue

            signal.validate()

            cursor = connection.execute(
                """
                INSERT INTO signals(
                    run_id,
                    symbol,
                    strategy,
                    side,
                    signal_time,
                    confidence,
                    accepted,
                    rejection_reason,
                    features_json
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    1, NULL, ?
                )
                """,
                (
                    run_id,
                    normalized_symbol,
                    signal.strategy,
                    signal.side.upper(),
                    bar.time.isoformat(),
                    signal.confidence,
                    json.dumps(
                        signal.metadata,
                        sort_keys=True,
                    ),
                ),
            )

            pending = _PendingSignal(
                signal=signal,
                signal_id=int(
                    cursor.lastrowid
                ),
                signal_time=bar.time,
            )

        if (
            open_trade is not None
            and selected_settings.force_close_at_end
        ):
            final_bar = bars[-1]

            holding_bars = (
                len(bars)
                - open_trade.entry_index
            )

            closed = _close_trade(
                trade=open_trade,
                bar=final_bar,
                raw_exit_price=(
                    final_bar.close
                ),
                result="END_OF_DATA",
                holding_bars=holding_bars,
                settings=selected_settings,
            )

            connection.execute(
                """
                UPDATE trades
                SET
                    exit_time = ?,
                    exit_price = ?,
                    gross_r = ?,
                    fee_r = ?,
                    slippage_r = ?,
                    net_r = ?,
                    result = ?,
                    metadata_json = ?
                WHERE id = ?
                """,
                (
                    closed.exit_time.isoformat(),
                    closed.exit_price,
                    closed.gross_r,
                    closed.fee_r,
                    closed.slippage_r,
                    closed.net_r,
                    closed.result,
                    json.dumps(
                        {
                            "raw_entry_price": (
                                closed.raw_entry_price
                            ),
                            "raw_exit_price": (
                                closed.raw_exit_price
                            ),
                            "holding_bars": (
                                closed.holding_bars
                            ),
                        },
                        sort_keys=True,
                    ),
                    closed.trade_id,
                ),
            )

            results.append(
                closed
            )

        connection.execute(
            """
            UPDATE runs
            SET
                finished_at = ?,
                status = 'FINISHED',
                notes = ?
            WHERE id = ?
            """,
            (
                utc_now(),
                (
                    f"bars={len(bars)} "
                    f"trades={len(results)}"
                ),
                run_id,
            ),
        )

    metrics = calculate(
        trade.net_r
        for trade in results
    )

    return ReplayReport(
        run_id=run_id,
        dataset=dataset,
        symbol=normalized_symbol,

        first_time=bars[0].time,
        last_time=bars[-1].time,

        bars=len(bars),
        trades=tuple(
            results
        ),
        metrics=metrics,
    )
