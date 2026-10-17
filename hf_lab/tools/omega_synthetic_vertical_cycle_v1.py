"""Bounded synthetic-only replay -> reject -> learning memory demo.

NOT a research/search authorization, not a market backtest, and not paper
trading. Never stores a synthetic outcome in JARVIS production learning memory.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import runpy
import tempfile

from hf_lab.tools import omega_stage03_engineering_smoke_v1 as smoke

STATE = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
LEARNING_MODULE = (smoke.ROOT /
    'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_learning_memory_v2.py')
GLOBAL = smoke.ROOT / 'research_agent_v57_quantum_searcher/tools/v57_jarvis/global'


def inspect_synthetic_shadow(replay_db: Path) -> int:
    """Consume only this run's synthetic SQLite trades, with no broker adapter."""
    shadow = runpy.run_path(str(GLOBAL / 'v57_shadow_core_v1.py'))
    monitor = runpy.run_path(str(GLOBAL / 'v57_monitoring_drift_core_v1.py'))
    execution = runpy.run_path(str(GLOBAL / 'v57_execution_core_v1.py'))
    with sqlite3.connect(replay_db) as connection:
        rows = connection.execute(
            "SELECT id,side,entry_time,entry_price,stop_price,target_price "
            "FROM trades WHERE result!='OPEN' ORDER BY id"
        ).fetchall()
    if len(rows) != 83:
        raise RuntimeError('SYNTHETIC_SHADOW_TRADE_COUNT_CHANGED')
    ids = set()
    dedup = execution['Deduplicator']()
    for trade_id, side, timestamp, entry, stop, target in rows:
        event = shadow['ShadowEvent'](
            strategy_id='SYNTHETIC_ONLY',
            symbol='SYNTHETIC_NOT_MARKET',
            side=side,
            volume=0.01,
            expected_entry=entry,
            observed_price=entry,
            spread=0.02,  # invented synthetic constant, not observed spread
            latency_ms=20.0,  # invented synthetic constant, not observed latency
            ts=timestamp,
        )
        checked = shadow['evaluate'](event, 0.05, 100.0, 0.02)
        if (checked.get('status') != 'SHADOW_OK'
                or checked.get('orders_allowed') is not False
                or checked.get('promotion_allowed') is not False
                or checked.get('event_id') in ids):
            raise RuntimeError('SYNTHETIC_SHADOW_REJECTED')
        ids.add(checked['event_id'])
        intent = execution['Intent'](
            strategy_id='SYNTHETIC_ONLY', symbol='SYNTHETIC_NOT_MARKET',
            side=side, volume=0.01, sl=stop, tp=target,
            nonce='SIMULATION_ONLY_' + str(trade_id),
        )
        validated = execution['validate'](intent, 'AUTHORIZE', mode='SHADOW')
        if (validated.get('status') != 'ACCEPT_SHADOW'
                or validated.get('send_allowed') is not False
                or not dedup.accept(intent)
                or dedup.accept(intent)):
            raise RuntimeError('SYNTHETIC_INTENT_REJECTED_OR_DUPLICATED')
    health = monitor['assess'](monitor['Health'](
        data_age_s=1, heartbeat_age_s=1, execution_divergences=0,
        drawdown=0.01, expected_trade_rate=10, observed_trade_rate=10,
    ))
    if (health.get('state') != 'NORMAL'
            or health.get('action') != 'KEEP'
            or health.get('orders_allowed') is not False):
        raise RuntimeError('SYNTHETIC_MONITOR_STOP')
    return len(ids)


def guarded_synthetic_cycle(state: Path, *, cycles: int = 3) -> dict:
    """Run one bounded fictitious replay then three deduplicated memory ticks."""
    if cycles != 3:
        raise ValueError('FIXED_SYNTHETIC_CYCLE_BUDGET_IS_THREE')
    auth = json.loads((state / 'search_authorization_v1.json').read_text())
    runner = json.loads((state / 'research_continuous_runner_v1.json').read_text())
    safe = (
        auth.get('status') == 'DENIED'
        and auth.get('authorized') is False
        and auth.get('max_candidates') == 0
        and auth.get('execution_started') is False
        and all(auth.get(key) is False for key in (
            'orders_allowed', 'mt5_allowed', 'holdout_allowed',
        ))
        and runner.get('status') == 'SAFE_IDLE'
        and runner.get('search_executed') is False
    )
    if not safe:
        raise RuntimeError('SYNTHETIC_STOP_UNSAFE_SCIENTIFIC_STATE')

    with tempfile.TemporaryDirectory(prefix='omega-synth-cycle-') as tmp:
        temp = Path(tmp)
        fingerprint, trades, signals, _ = smoke.exercise(
            temp / 'synthetic_replay.sqlite3', smoke.synthetic_bars()
        )
        if (trades, signals) != (83, 83):
            raise RuntimeError('SYNTHETIC_REPLAY_OUTPUT_CHANGED')
        shadow_events = inspect_synthetic_shadow(temp / 'synthetic_replay.sqlite3')
        evidence = temp / 'evidence'
        evidence.mkdir()
        (evidence / 'synthetic_reject.json').write_text(json.dumps({
            'kind': 'SYNTHETIC_ONLY_REJECT',
            'space': 'SYNTHETIC_ONLY',
            'status': 'ENGINEERING_PASS_SCIENCE_UNADMITTED',
            'replay_fingerprint_sha256': fingerprint,
            'result': {'batches': [{'candidates': [{
                'strategy_id': 'SYNTHETIC_NOT_REAL',
                'decision': 'REJECT',
                'deep_status': 'NO_INDEPENDENT_MARKET_EVIDENCE',
            }]}]},
            'research_execution_authorized': False,
            'orders_allowed': False,
        }, sort_keys=True))
        ingest = runpy.run_path(str(LEARNING_MODULE))['ingest']
        ingest.__globals__['DB'] = temp / 'learning.sqlite3'
        ticks = [ingest(evidence) for _ in range(cycles)]
        if ticks != [(1, 1), (0, 1), (0, 1)]:
            raise RuntimeError('SYNTHETIC_MEMORY_DEDUP_FAILED')
    # Verify the external gate has not changed before reporting PASS.
    after = json.loads((state / 'search_authorization_v1.json').read_text())
    if after != auth:
        raise RuntimeError('SCIENTIFIC_GATE_CHANGED_DURING_TEST')
    return {
        'kind': 'OMEGA_SYNTHETIC_VERTICAL_CYCLE_V1',
        'status': 'ENGINEERING_PASS_NOT_SCIENTIFIC_ADMISSION',
        'source': 'GENERATED_SYNTHETIC_BARS_ONLY',
        'cycles': cycles,
        'replay_executions': 1,
        'closed_synthetic_trades': trades,
        'verified_synthetic_shadow_events': shadow_events,
        'synthetic_shadow_no_broker_adapter': True,
        'learning_ticks_inserted': [a for a, _ in ticks],
        'learned_observations': ticks[-1][1],
        'dedup_replay_skips': cycles - 1,
        'synthetic_replay_fingerprint_sha256': fingerprint,
        'market_data_accessed': False,
        'production_learning_memory_modified': False,
        'scientific_candidate_admitted': False,
        'search_executed': False,
        'holdout_allowed': False,
        'mt5_allowed': False,
        'orders_allowed': False,
        'real_orders_executed': False,
    }


def main() -> None:
    result = guarded_synthetic_cycle(STATE)
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
