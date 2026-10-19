"""Bounded synthetic-only replay -> reject -> learning memory demo.

NOT a research/search authorization, not a market backtest, and not paper
trading. Never stores a synthetic outcome in JARVIS production learning memory.
"""
from __future__ import annotations

import json
import sqlite3
import math
from datetime import datetime, timezone

from hf_lab.replay import ReplaySettings, run_replay
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


def compare_cost_stress(base_db: Path, stress_db: Path, baseline_metrics: dict) -> dict:
    """One additional *synthetic-only* cost stress. Veto, never optimize fees."""
    stress=ReplaySettings(fee_bps_per_side=20.0,slippage_bps_per_side=5.0,
                          shadow_only=True,allow_real_orders=False)
    report=run_replay(symbol='BTCUSD',dataset='SYNTHETIC_STAGE04_COST_REVIEW_ONLY',
                      bars=smoke.synthetic_bars(),strategy=smoke.momentum_burst,
                      settings=stress,database_path=stress_db)
    # Independent SQLite reconciliation: never accept summary fields on trust.
    sql=("SELECT side,signal_time,entry_time,exit_time,gross_r,fee_r,"
         "slippage_r,net_r FROM trades WHERE result!='OPEN' ORDER BY id")
    with sqlite3.connect(base_db) as db:
        base=db.execute(sql).fetchall()
    with sqlite3.connect(stress_db) as db:
        stressed_rows=db.execute(sql).fetchall()
    stressed=list(report.trades)
    if len(base)!=83 or len(stressed)!=83 or len(stressed_rows)!=83:
        raise RuntimeError('STAGE04_TRADE_COUNT_CHANGED')
    def independently_reconcile(rows, expected):
        net_values=[]
        last_exit=None
        for row in rows:
            side, signal, entry, exit_, gross, fee, slip, net=row
            if side not in ('BUY','SELL'):
                raise RuntimeError('STAGE06_INVALID_TRADE_DIRECTION')
            try:
                times=[datetime.fromisoformat(x) for x in (signal,entry,exit_)]
            except (TypeError,ValueError) as exc:
                raise RuntimeError('STAGE06_INVALID_SYNTHETIC_TIMESTAMP') from exc
            if (any(t.tzinfo is None or t.utcoffset()!=timezone.utc.utcoffset(t)
                    for t in times)
                    or not times[0]<times[1]<=times[2]
                    or (last_exit is not None and times[1]<last_exit)):
                raise RuntimeError('STAGE06_TEMPORAL_INTEGRITY_REJECT')
            last_exit=times[2]
            if (any(type(v) not in (int,float) or not math.isfinite(v)
                    for v in (gross,fee,slip,net))
                    or not math.isclose(net,gross-fee-slip,rel_tol=1e-10,abs_tol=1e-10)
                    or fee<0 or slip<0):
                raise RuntimeError('STAGE06_TRADE_ACCOUNTING_REJECT')
            net_values.append(net)
        wins=sum(v>0 for v in net_values)
        gains=sum(max(0.0,v) for v in net_values)
        losses=-sum(min(0.0,v) for v in net_values)
        if not losses>0:
            raise RuntimeError('STAGE06_PROFIT_FACTOR_UNREPORTABLE')
        equity=peak=drawdown=0.0
        for value in net_values:
            equity+=value
            peak=max(equity,peak)
            drawdown=max(drawdown,peak-equity)
        recalculated={'net_r':sum(net_values),
                      'profit_factor':gains/losses,
                      'trades':len(rows),'wins':wins,
                      'losses':len(rows)-wins,
                      'max_drawdown_r':drawdown}
        for key,value in recalculated.items():
            observed=expected[key] if isinstance(expected,dict) else getattr(expected,key)
            if (type(observed) not in (int,float) or not math.isfinite(observed)
                    or not math.isclose(observed,value,rel_tol=1e-10,abs_tol=1e-10)):
                raise RuntimeError('STAGE06_INDEPENDENT_METRICS_MISMATCH_'+key.upper())
        return recalculated
    base_independent=independently_reconcile(base,baseline_metrics)
    stress_independent=independently_reconcile(stressed_rows,report.metrics)
    for initial,modified,persisted in zip(base,stressed,stressed_rows,strict=True):
        # Causal timestamps, gross trade and fills must not change under costs.
        a_side,a_signal,a_entry,a_exit,a_gross,a_fee,a_slip,a_net=initial
        actual=(modified.side,modified.signal_time.isoformat(),
                modified.entry_time.isoformat(),modified.exit_time.isoformat())
        expected=(a_side,a_signal,a_entry,a_exit)
        if (actual!=expected or persisted[:4]!=expected
                or not math.isclose(modified.net_r,persisted[-1],rel_tol=1e-10,abs_tol=1e-10)
                or not math.isclose(a_gross,persisted[4],rel_tol=1e-10,abs_tol=1e-10)):
            raise RuntimeError('STAGE04_REPLAY_PATH_OR_NUMERIC_MISMATCH')
        if persisted[-1]>=a_net or persisted[5]<a_fee or persisted[6]<a_slip:
            raise RuntimeError('STAGE04_HIGHER_COST_DID_NOT_REDUCE_NET_TRADE')
    base_net=base_independent['net_r']
    stress_net=stress_independent['net_r']
    base_pf=base_independent['profit_factor']
    stress_pf=stress_independent['profit_factor']
    if not (base_net>0>stress_net and base_pf>1>stress_pf>=0):
        raise RuntimeError('STAGE04_COST_FRAGILITY_VETO_NOT_DEMONSTRATED')
    return {
        'kind':'OMEGA_STAGE04_SYNTHETIC_COST_STRESS_V1',
        'status':'CONTROLLED_COMPARISON_REJECT_COST_FRAGILITY',
        'source':'SYNTHETIC_BARS_ONLY',
        'comparison_budget':1,
        'baseline_fee_bps_per_side':5.0,
        'baseline_slippage_bps_per_side':1.0,
        'stressed_fee_bps_per_side':20.0,
        'stressed_slippage_bps_per_side':5.0,
        'baseline_trades':len(base),
        'stressed_trades':len(stressed),
        'baseline_net_r':base_net,
        'stressed_net_r':stress_net,
        'baseline_pf_synthetic':base_pf,
        'stressed_pf_synthetic':stress_pf,
        'path_identical':True,
        'every_trade_worsened':True,
        'stage06_independent_sqlite_metrics_verified':True,
        'stage06_temporal_integrity_verified':True,
        'stage06_holdout_or_market_data_read':False,
        'decision':'REJECT_SYNTHETIC_COST_FRAGILITY',
        'improvement_claimed':False,
        'scientific_admission':False,
        'orders_allowed':False,'holdout_allowed':False,
    }


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
        and all(runner.get(key) is not True for key in (
            'orders_allowed','mt5_allowed','holdout_allowed'
        ))
    )
    if not safe:
        raise RuntimeError('SYNTHETIC_STOP_UNSAFE_SCIENTIFIC_STATE')

    with tempfile.TemporaryDirectory(prefix='omega-synth-cycle-') as tmp:
        temp = Path(tmp)
        baseline_db=temp / 'synthetic_replay.sqlite3'
        fingerprint, trades, signals, diagnostic = smoke.exercise(
            baseline_db, smoke.synthetic_bars()
        )
        if (trades, signals) != (83, 83):
            raise RuntimeError('SYNTHETIC_REPLAY_OUTPUT_CHANGED')
        shadow_events = inspect_synthetic_shadow(baseline_db)
        cost_stress = compare_cost_stress(baseline_db,temp / 'stress_replay.sqlite3',diagnostic)
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
                'deep_status': 'SYNTHETIC_COST_FRAGILITY_REJECT_NO_SCIENTIFIC_ADMISSION',
            }]}]},
            'research_execution_authorized': False,
            'orders_allowed': False,
        }, sort_keys=True))
        ingest = runpy.run_path(str(LEARNING_MODULE))['ingest']
        ingest.__globals__['DB'] = temp / 'learning.sqlite3'
        ticks = [ingest(evidence) for _ in range(cycles)]
        if ticks != [(1, 1), (0, 1), (0, 1)]:
            raise RuntimeError('SYNTHETIC_MEMORY_DEDUP_FAILED')
        with sqlite3.connect(temp / 'learning.sqlite3') as mem:
            decisions=mem.execute('SELECT decision, reason FROM observations').fetchall()
        if decisions!=[('REJECT','SYNTHETIC_COST_FRAGILITY_REJECT_NO_SCIENTIFIC_ADMISSION')]:
            raise RuntimeError('STAGE04_COST_STRESS_MEMORY_DECISION_MISSING')
    # Verify the external gate has not changed before reporting PASS.
    after = json.loads((state / 'search_authorization_v1.json').read_text())
    if after != auth:
        raise RuntimeError('SCIENTIFIC_GATE_CHANGED_DURING_TEST')
    # Autonomous runner may wake during this synthetic cycle. Fail closed
    # rather than claim engineering PASS if discovery/phase2 has started.
    now_runner = json.loads((state / 'research_continuous_runner_v1.json').read_text())
    if (now_runner.get('status')!='SAFE_IDLE'
            or now_runner.get('search_executed') is not False
            or any(now_runner.get(key) is True for key in (
                'orders_allowed','mt5_allowed','holdout_allowed'))):
        raise RuntimeError('RUNNER_STATE_CHANGED_DURING_TEST')
    return {
        'kind': 'OMEGA_SYNTHETIC_VERTICAL_CYCLE_V1',
        'status': 'ENGINEERING_PASS_NOT_SCIENTIFIC_ADMISSION',
        'source': 'GENERATED_SYNTHETIC_BARS_ONLY',
        'cycles': cycles,
        'replay_executions': 2,
        'stage04_cost_stress':cost_stress,
        'stage04_comparison_executions':1,
        'closed_synthetic_trades': trades,
        'verified_synthetic_shadow_events': shadow_events,
        'synthetic_shadow_no_broker_adapter': True,
        'learning_ticks_inserted': [a for a, _ in ticks],
        'learned_observations': ticks[-1][1],
        'stage04_learning_decision':decisions[0][0],
        'stage04_learning_reason':decisions[0][1],
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
