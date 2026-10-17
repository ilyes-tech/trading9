"""Stage09 engineering: fictitious shadow monitoring, NEVER broker/paper/live.

Reuses existing replay and global shadow/drift/intent/digital-twin functions.
Tests use solely local generated price bars and temporary SQLite.
"""
from __future__ import annotations

from pathlib import Path
import runpy
import pytest

from hf_lab.replay import run_replay
from hf_lab.tools import omega_stage03_engineering_smoke_v1 as smoke

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = ROOT / 'research_agent_v57_quantum_searcher/tools/v57_jarvis/global'
SHADOW = runpy.run_path(str(GLOBAL / 'v57_shadow_core_v1.py'))
DRIFT = runpy.run_path(str(GLOBAL / 'v57_monitoring_drift_core_v1.py'))
EXEC = runpy.run_path(str(GLOBAL / 'v57_execution_core_v1.py'))


def synthetic_trades(tmp_path):
    report = run_replay(
        symbol='SYNTHETIC_ONLY',
        dataset='STAGE09_NO_MARKET_DATA',
        bars=smoke.synthetic_bars(),
        strategy=smoke.momentum_burst,
        settings=smoke.SETTINGS,
        database_path=tmp_path / 'stage09.sqlite3',
    )
    assert report.metrics.trades == 83
    assert len(report.trades) == 83
    return report.trades


def make_event(trade, *, spread=0.02, latency_ms=20.0, gap=0.01):
    return SHADOW['ShadowEvent'](
        strategy_id='SYNTHETIC_ONLY',
        symbol='FAKE_SYNTHETIC_MARKET',
        side=trade.side,
        volume=0.01,
        expected_entry=trade.raw_entry_price,
        observed_price=trade.raw_entry_price + gap,
        spread=spread,
        latency_ms=latency_ms,
        ts=trade.entry_time.isoformat(),
    )


def test_synthetic_83_trade_shadow_events_are_repeatable_without_orders(tmp_path):
    trades = synthetic_trades(tmp_path)
    first = [SHADOW['evaluate'](make_event(t), 0.05, 100, 0.02) for t in trades]
    second = [SHADOW['evaluate'](make_event(t), 0.05, 100, 0.02) for t in trades]
    assert first == second
    assert len(first) == 83
    assert len({event['event_id'] for event in first}) == 83
    assert all(event['status'] == 'SHADOW_OK' for event in first)
    assert all(event['orders_allowed'] is False and event['promotion_allowed'] is False for event in first)


def test_synthetic_shadow_spread_latency_and_price_gap_are_rejected_or_degraded(tmp_path):
    first = synthetic_trades(tmp_path)[0]
    for override,reason in (({'spread':0.50},'SPREAD'),
                            ({'latency_ms':1000.0},'LATENCY'),
                            ({'gap':0.25},'PRICE_GAP')):
        event=SHADOW['evaluate'](make_event(first,**override),0.05,100,0.02)
        assert event['status'] == 'SHADOW_DEGRADED'
        assert reason in event['reasons']
        assert event['orders_allowed'] is False and event['promotion_allowed'] is False
    invalid=SHADOW['evaluate'](make_event(first,spread=-1),0.05,100,0.02)
    assert invalid['status']=='REJECT' and invalid['orders_allowed'] is False


@pytest.mark.parametrize('health,expected_action,reason', [
    ((1,1,0,0.01,10,10),'KEEP',None),
    ((200,1,0,0.01,10,10),'QUARANTINE','STALE_DATA'),
    ((1,90,0,0.01,10,10),'STOP','HEARTBEAT_LOST'),
    ((1,1,1,0.01,10,10),'QUARANTINE','EXECUTION_DIVERGENCE'),
    ((1,1,0,0.2,10,10),'STOP','DRAWDOWN_LIMIT'),
    ((1,1,0,0.01,10,100),'QUARANTINE','TRADE_RATE_DRIFT'),
])
def test_synthetic_monitor_action_on_failures(health,expected_action,reason):
    state=DRIFT['assess'](DRIFT['Health'](*health))
    assert state['action']==expected_action
    assert state['orders_allowed'] is False and state['promotion_allowed'] is False
    if reason:
        assert reason in state['reasons']


def test_broker_send_is_always_disabled_even_with_healthy_synthetic_intent(tmp_path):
    trade=synthetic_trades(tmp_path)[0]
    intent=EXEC['Intent'](
        strategy_id='SYNTHETIC_ONLY', symbol='FAKE_SYNTHETIC_MARKET',
        side=trade.side, volume=0.01, sl=100.0, tp=100.0,
        nonce='STAGE09_SIMULATED',
    )
    for mode in ('SHADOW','DEMO_DISABLED','LIVE_DISABLED'):
        validation=EXEC['validate'](intent,'AUTHORIZE',mode=mode)
        assert validation['status']=='ACCEPT_SHADOW'
        assert validation['send_allowed'] is False
    assert EXEC['validate'](intent,'AUTHORIZE',mode='LIVE')['status']=='DENY'
    assert EXEC['validate'](intent,'DENY')['status']=='DENY'
    assert EXEC['validate'](intent,'AUTHORIZE',market_fresh=False)['status']=='DENY'
    assert EXEC['validate'](intent,'AUTHORIZE',broker_healthy=False)['status']=='DENY'
    d=EXEC['Deduplicator']()
    assert d.accept(intent) and not d.accept(intent)


def test_digital_twin_catches_synthetic_mismatch_without_promotion():
    expected=[dict(symbol='FAKE',side='BUY',volume=0.01,entry=100.0,sl=99.0,tp=101.0)]
    equal=EXEC['digital_twin'](expected,[dict(expected[0])])
    assert equal['status']=='PARITY' and equal['promotion_allowed'] is False
    wrong=[dict(expected[0],entry=100.5)]
    fail=EXEC['digital_twin'](expected,wrong)
    assert fail['status']=='DIVERGENCE' and fail['promotion_allowed'] is False
    missing=EXEC['digital_twin'](expected,[])
    assert missing['status']=='DIVERGENCE' and missing['promotion_allowed'] is False


@pytest.mark.parametrize('bad', [float('nan'),float('inf'),-float('inf')])
def test_nonfinite_synthetic_shadow_values_never_look_healthy(tmp_path,bad):
    trade=synthetic_trades(tmp_path)[0]
    bad_event=make_event(trade,spread=bad)
    r=SHADOW['evaluate'](bad_event,0.05,100,0.02)
    assert r['status']=='REJECT'
    assert r['reason']=='INVALID_INPUT'
    assert r['orders_allowed'] is False and r['promotion_allowed'] is False
    bad_threshold=SHADOW['evaluate'](make_event(trade),float('nan'),100,0.02)
    assert bad_threshold['status']=='REJECT'
    assert bad_threshold['orders_allowed'] is False


@pytest.mark.parametrize('bad', [float('nan'),float('inf'),-float('inf')])
def test_nonfinite_monitoring_health_or_limits_emergency_stop(bad):
    state=DRIFT['assess'](DRIFT['Health'](bad,1,0,0.01,10,10))
    assert state['state']=='EMERGENCY' and state['action']=='STOP'
    assert state['reasons']==['INVALID_INPUT']
    assert state['orders_allowed'] is False and state['promotion_allowed'] is False
    limit=DRIFT['Thresholds'](max_heartbeat_age_s=bad)
    state=DRIFT['assess'](DRIFT['Health'](1,1,0,0.01,10,10),limit)
    assert state['action']=='STOP'


def test_nonpositive_shadow_volume_and_impossible_rate_not_accepted(tmp_path):
    trade=synthetic_trades(tmp_path)[0]
    from dataclasses import replace
    r=SHADOW['evaluate'](replace(make_event(trade),volume=0),0.05,100,0.02)
    assert r['status']=='REJECT' and r['orders_allowed'] is False
    drift=DRIFT['assess'](DRIFT['Health'](1,1,0,0.01,0,1))
    assert drift['action']=='QUARANTINE'
    assert 'TRADE_RATE_DRIFT' in drift['reasons']
