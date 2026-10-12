"""Integrated synthetic review; no historical replay or holdout access."""
import copy,os,runpy
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODULE=os.environ.get('OMEGA_COMPOSED_VERIFIER',str(ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_independent_evidence_verifier_v2.py'))
NS=runpy.run_path(MODULE);ASSESS=NS['assess_replay_evidence']
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def fixture():
    folds=[]
    for f in range(3):
        rows=[]
        for day in range(20):
            for i,move in enumerate((-0.01,0.03,0.03)):
                entry=(1000+f*30+day)*86400+i*120
                rows.append(dict(side='BUY',raw_entry_price=100.,entry_price=100.,raw_exit_price=100.+move,
                                 exit_price=100.+move,stop_price=99.,gross_r=move,net_r=move,fee_r=0.,slippage_r=0.,
                                 entry_time=iso(entry),exit_time=iso(entry+60),stress_net_bps=-9999))
        folds.append(rows)
    start=1000*86400;end=1080*86400
    manifest=dict(interval_basis='FULL_INFORMATION_SUPPORT',strategy_sha256='a'*64,dataset_sha256='b'*64,
                  embargo_seconds=10,previously_used=[dict(start=1,end=start-10)],
                  replication=dict(start=start,end=end),reserved_holdout=[dict(start=end+10,end=end+100)],
                  registered_at=start-1,first_replication_access_at=end+1)
    return folds,dict(fee_bps_per_side=0,slippage_bps_per_side=0),manifest
def test_full_path_deterministic_and_never_admitted():
    args=fixture();saved=copy.deepcopy(args);a=ASSESS(*args)
    assert a['status']=='REPLAY_CHECKS_PASS_SCIENTIFIC_REVIEW_BLOCKED'
    assert a==ASSESS(*args) and args==saved
    assert len(a['unresolved'])==5
    for k in ('new_research_authorized','independent_replication_proven','orders_allowed','holdout_allowed'):
        assert a[k] is False
def test_forged_return_is_ignored():
    args=fixture();a=ASSESS(*args)
    for fold in args[0]:
        for trade in fold:trade['stress_net_bps']=1e99
    assert ASSESS(*args)==a
def test_tampered_native_metric_fails_before_robustness():
    f,s,m=fixture();f[0][0]['net_r']=100
    out=ASSESS(f,s,m)
    assert out['reason']=='MISMATCH_NET_R'
    assert 'robustness' not in out['checks']
def test_unaware_fractional_and_outside_times():
    for value,reason in [('1972-09-27T00:00:00','INVALID_NATIVE_TIMESTAMPS'),
                         ('1972-09-27T00:00:00.500+00:00','INVALID_NATIVE_TIMESTAMPS'),
                         (iso(1),'TRADE_OUTSIDE_REPLICATION_INFORMATION_INTERVAL')]:
        f,s,m=fixture();f[0][0]['entry_time']=value
        assert ASSESS(f,s,m)['reason']==reason
def test_half_open_exit_boundary_rejected():
    f,s,m=fixture();f[-1][-1]['exit_time']=iso(m['replication']['end'])
    assert ASSESS(f,s,m)['reason']=='TRADE_OUTSIDE_REPLICATION_INFORMATION_INTERVAL'
def test_negative_arithmetically_valid_trades_fail_science():
    f,s,m=fixture()
    for fold in f:
        for t in fold:t.update(raw_exit_price=99.99,exit_price=99.99,gross_r=-0.01,net_r=-0.01)
    out=ASSESS(f,s,m)
    assert out['reason']=='ROBUSTNESS_CRITERIA_FAILED'
    assert out['checks']['cost_arithmetic']['status']=='COST_ARITHMETIC_VERIFIED_NOT_ADMITTED'
def test_temporal_and_resource_errors():
    f,s,m=fixture();m['registered_at']=m['first_replication_access_at']
    assert ASSESS(f,s,m)['reason']=='REGISTRATION_NOT_BEFORE_ACCESS'
    f,s,m=fixture()
    assert ASSESS([[],[],[]],s,m)['reason']=='THREE_NONEMPTY_FOLDS_REQUIRED'
    assert ASSESS([[{}]*100001,[{}],[{}]],s,m)['reason']=='TRADE_BUDGET_EXCEEDED'
    assert ASSESS(f,None,m)['reason']=='MISSING_COST_SETTINGS'
def test_risk_units_convert_to_notional_bps():
    f,s,m=fixture();original=ASSESS(f,s,m)
    for fold in f:
        for t in fold:
            t['stop_price']=98.
            t['gross_r']/=2;t['net_r']/=2
    assert ASSESS(f,s,m)==original
