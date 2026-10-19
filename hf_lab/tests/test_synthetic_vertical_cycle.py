"""Synthetic-only finite orchestrator: no market/MT5/holdout paths."""
import json
from pathlib import Path

import pytest

from hf_lab.tools.omega_synthetic_vertical_cycle_v1 import guarded_synthetic_cycle


def safe_state(path: Path):
    (path / 'search_authorization_v1.json').write_text(json.dumps({
        'status': 'DENIED', 'authorized': False, 'max_candidates': 0,
        'execution_started': False, 'orders_allowed': False,
        'mt5_allowed': False, 'holdout_allowed': False,
    }))
    (path / 'research_continuous_runner_v1.json').write_text(json.dumps({
        'status': 'SAFE_IDLE', 'search_executed': False,
    }))


def test_bounded_synthetic_vertical_replay_memory_reject_and_idempotency(tmp_path):
    safe_state(tmp_path)
    result = guarded_synthetic_cycle(tmp_path)
    assert result['status'] == 'ENGINEERING_PASS_NOT_SCIENTIFIC_ADMISSION'
    assert result['source'] == 'GENERATED_SYNTHETIC_BARS_ONLY'
    assert result['cycles'] == 3
    assert result['replay_executions'] == 2  # original + one fixed-cost stress
    assert result['stage04_comparison_executions'] == 1
    cost = result['stage04_cost_stress']
    assert cost['decision'] == 'REJECT_SYNTHETIC_COST_FRAGILITY'
    assert cost['comparison_budget'] == 1
    assert cost['baseline_trades'] == cost['stressed_trades'] == 83
    assert cost['path_identical'] and cost['every_trade_worsened']
    assert cost['baseline_net_r'] > 0 > cost['stressed_net_r']
    assert cost['baseline_pf_synthetic'] > 1 > cost['stressed_pf_synthetic']
    assert cost['improvement_claimed'] is False
    assert cost['scientific_admission'] is False
    assert cost['orders_allowed'] is False
    assert result['closed_synthetic_trades'] == 83
    assert result['verified_synthetic_shadow_events'] == 83
    assert result['synthetic_shadow_no_broker_adapter'] is True
    assert result['learning_ticks_inserted'] == [1, 0, 0]
    assert result['learned_observations'] == 1
    assert result['stage04_learning_decision'] == 'REJECT'
    assert result['stage04_learning_reason'] == 'SYNTHETIC_COST_FRAGILITY_REJECT_NO_SCIENTIFIC_ADMISSION'
    assert result['dedup_replay_skips'] == 2
    assert all(result[key] is False for key in (
        'market_data_accessed', 'production_learning_memory_modified',
        'scientific_candidate_admitted', 'search_executed',
        'holdout_allowed', 'mt5_allowed', 'orders_allowed',
        'real_orders_executed',
    ))
    assert not list(tmp_path.glob('*.sqlite3'))


@pytest.mark.parametrize('mutation', [
    ('search_authorization_v1.json', 'status', 'AUTHORIZED'),
    ('search_authorization_v1.json', 'authorized', True),
    ('search_authorization_v1.json', 'max_candidates', 1),
    ('search_authorization_v1.json', 'orders_allowed', True),
    ('search_authorization_v1.json', 'holdout_allowed', True),
    ('research_continuous_runner_v1.json', 'status', 'STOP_FAIL'),
    ('research_continuous_runner_v1.json', 'search_executed', True),
])
def test_refuses_unsafe_or_live_permissions_before_replay(tmp_path, monkeypatch, mutation):
    safe_state(tmp_path)
    path = tmp_path / mutation[0]
    doc = json.loads(path.read_text())
    doc[mutation[1]] = mutation[2]
    path.write_text(json.dumps(doc))
    def forbidden(*args, **kwargs):
        raise AssertionError('NO_REPLAY_ON_UNSAFE_STATE')
    monkeypatch.setattr('hf_lab.tools.omega_synthetic_vertical_cycle_v1.smoke.exercise', forbidden)
    with pytest.raises(RuntimeError, match='SYNTHETIC_STOP_UNSAFE_SCIENTIFIC_STATE'):
        guarded_synthetic_cycle(tmp_path)


def test_cycle_budget_fail_closed(tmp_path):
    safe_state(tmp_path)
    for invalid in (0, 1, 2, 4, 100):
        with pytest.raises(ValueError, match='FIXED_SYNTHETIC_CYCLE_BUDGET'):
            guarded_synthetic_cycle(tmp_path, cycles=invalid)



def test_replay_failure_aborts_before_learning(tmp_path, monkeypatch):
    safe_state(tmp_path)
    def interrupted(*args, **kwargs):
        raise RuntimeError('SYNTHETIC_REPLAY_INTERRUPTED')
    monkeypatch.setattr(
        'hf_lab.tools.omega_synthetic_vertical_cycle_v1.smoke.exercise',
        interrupted,
    )
    with pytest.raises(RuntimeError, match='SYNTHETIC_REPLAY_INTERRUPTED'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))


def test_gate_change_during_synthetic_replay_fails_closed(tmp_path, monkeypatch):
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle
    safe_state(tmp_path)
    real = cycle.smoke.exercise

    def race(*args, **kwargs):
        result = real(*args, **kwargs)
        p = tmp_path / 'search_authorization_v1.json'
        d = json.loads(p.read_text())
        d['authorized'] = True
        p.write_text(json.dumps(d))
        return result

    monkeypatch.setattr(cycle.smoke, 'exercise', race)
    with pytest.raises(RuntimeError, match='SCIENTIFIC_GATE_CHANGED_DURING_TEST'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))



def test_runner_wake_during_synthetic_work_fails_closed(tmp_path,monkeypatch):
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle
    safe_state(tmp_path)
    real=cycle.smoke.exercise

    def concurrent_runner(*args,**kwargs):
        value=real(*args,**kwargs)
        path=tmp_path/'research_continuous_runner_v1.json'
        doc=json.loads(path.read_text())
        doc['status']='RESEARCH_CYCLE_COMPLETED'
        doc['search_executed']=True
        path.write_text(json.dumps(doc))
        return value

    monkeypatch.setattr(cycle.smoke,'exercise',concurrent_runner)
    with pytest.raises(RuntimeError,match='RUNNER_STATE_CHANGED_DURING_TEST'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))


def test_unsafe_runner_permission_refused_before_replay(tmp_path,monkeypatch):
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle
    for flag in ('orders_allowed','mt5_allowed','holdout_allowed'):
        safe_state(tmp_path)
        runner=tmp_path/'research_continuous_runner_v1.json'
        doc=json.loads(runner.read_text())
        doc[flag]=True
        runner.write_text(json.dumps(doc))
        monkeypatch.setattr(cycle.smoke,'exercise',lambda *a,**k:
                            (_ for _ in ()).throw(AssertionError('UNSAFE_REPLAY_STARTED')))
        with pytest.raises(RuntimeError,match='SYNTHETIC_STOP_UNSAFE_SCIENTIFIC_STATE'):
            guarded_synthetic_cycle(tmp_path)


def test_shadow_failure_fails_closed_before_memory(tmp_path, monkeypatch):
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle
    safe_state(tmp_path)
    def unsafe(*args, **kwargs):
        raise RuntimeError('SYNTHETIC_MONITOR_STOP')
    monkeypatch.setattr(cycle, 'inspect_synthetic_shadow', unsafe)
    with pytest.raises(RuntimeError, match='SYNTHETIC_MONITOR_STOP'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))


def test_shadow_count_mismatch_fails_closed(tmp_path, monkeypatch):
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle
    safe_state(tmp_path)
    old=cycle.smoke.exercise
    def bad_count(*args, **kwargs):
        result=old(*args,**kwargs)
        import sqlite3
        with sqlite3.connect(args[0]) as c:
            c.execute('DELETE FROM trades WHERE id=(SELECT MIN(id) FROM trades)')
        return result
    monkeypatch.setattr(cycle.smoke, 'exercise', bad_count)
    with pytest.raises(RuntimeError, match='SYNTHETIC_SHADOW_TRADE_COUNT_CHANGED'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))



def test_repeated_integrated_synthetic_cycles_produce_same_evidence(tmp_path):
    safe_state(tmp_path)
    first = guarded_synthetic_cycle(tmp_path)
    second = guarded_synthetic_cycle(tmp_path)
    assert first == second
    assert first['verified_synthetic_shadow_events'] == 83
    assert first['learning_ticks_inserted'] == [1, 0, 0]
    assert first['orders_allowed'] is False
    assert first['real_orders_executed'] is False


def test_stage04_rejects_modified_trade_path_before_learning(tmp_path,monkeypatch):
    from dataclasses import replace
    from datetime import timedelta
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle

    safe_state(tmp_path)
    real=cycle.run_replay

    def tampered(*args,**kwargs):
        out=real(*args,**kwargs)
        trades=list(out.trades)
        trades[0]=replace(trades[0],entry_time=trades[0].entry_time+timedelta(minutes=1))
        return replace(out,trades=tuple(trades))

    monkeypatch.setattr(cycle,'run_replay',tampered)
    with pytest.raises(RuntimeError,match='STAGE04_REPLAY_PATH_OR_NUMERIC_MISMATCH'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))


def test_stage04_rejects_false_cost_robustness_or_unexpected_profit(tmp_path,monkeypatch):
    from dataclasses import replace
    from hf_lab.tools import omega_synthetic_vertical_cycle_v1 as cycle

    safe_state(tmp_path)
    real=cycle.run_replay

    def tampered(*args,**kwargs):
        out=real(*args,**kwargs)
        metrics=replace(out.metrics,net_r=3.0,profit_factor=2.0)
        return replace(out,metrics=metrics)

    monkeypatch.setattr(cycle,'run_replay',tampered)
    with pytest.raises(RuntimeError,match='STAGE04_COST_FRAGILITY_VETO_NOT_DEMONSTRATED'):
        guarded_synthetic_cycle(tmp_path)
    assert not list(tmp_path.glob('*.sqlite3'))
