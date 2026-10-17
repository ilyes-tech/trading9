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
    assert result['replay_executions'] == 1
    assert result['closed_synthetic_trades'] == 83
    assert result['learning_ticks_inserted'] == [1, 0, 0]
    assert result['learned_observations'] == 1
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
