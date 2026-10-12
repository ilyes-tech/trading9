"""Synthetic information-interval tests; no dataset or holdout access."""
import copy,os,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODULE=Path(os.environ.get('OMEGA_TEMPORAL_VERIFIER',str(ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_independent_evidence_verifier_v2.py')))
AUDIT=runpy.run_path(str(MODULE))['audit_temporal_separation']
def fixture():
    return dict(interval_basis='FULL_INFORMATION_SUPPORT',strategy_sha256='a'*64,dataset_sha256='b'*64,
                embargo_seconds=10,previously_used=[dict(start=100,end=200),dict(start=20,end=90)],
                replication=dict(start=210,end=300),reserved_holdout=[dict(start=310,end=400)],
                registered_at=201,first_replication_access_at=301)
def rejected(m,reason):
    r=AUDIT(m)
    assert r['status']=='TEMPORAL_METADATA_REJECTED'
    assert r['reason']==reason
    assert r['new_research_authorized'] is False
def test_boundary_pass_does_not_prove_independence():
    r=AUDIT(fixture())
    assert r['status']=='TEMPORAL_METADATA_VERIFIED_NOT_ADMITTED'
    for key,value in r.items():
        if key.endswith(('_verified','_proven','_authorized','_allowed')):assert value is False
def test_prior_overlap_and_feature_lookback():
    for start in (190,200,209):
        m=fixture();m['replication']['start']=start
        rejected(m,'PRIOR_INFORMATION_OVERLAP_OR_EMBARGO')
def test_holdout_overlap_and_embargo():
    for start in (220,299,300,309):
        m=fixture();m['reserved_holdout'][0]['start']=start
        rejected(m,'HOLDOUT_OVERLAP_OR_EMBARGO')
def test_registration_must_precede_access():
    for registered in (301,302,True,None):
        m=fixture();m['registered_at']=registered
        rejected(m,'REGISTRATION_NOT_BEFORE_ACCESS')
    m=fixture();m['first_replication_access_at']=299
    rejected(m,'ACCESS_BEFORE_COMPLETE_INTERVAL')
def test_incomplete_registry_and_budgets():
    for key,reason in [('previously_used','INVALID_PRIOR_INTERVALS'),('reserved_holdout','INVALID_HOLDOUT_INTERVALS')]:
        for value in ([],None,[dict(start=1,end=2)]*10001):
            m=fixture();m[key]=value;rejected(m,reason)
def test_invalid_intervals_fail_closed():
    for value in (None,{},dict(start=True,end=300),dict(start=210,end=210),dict(start=-1,end=300),dict(start=210,end=float('inf'))):
        m=fixture();m['replication']=value;rejected(m,'INVALID_REPLICATION_INTERVAL')
def test_contract_and_hash_validation():
    rejected(None,'MALFORMED_MANIFEST')
    m=fixture();m['interval_basis']='ENTRY_TIMES_ONLY';rejected(m,'MISSING_INFORMATION_SUPPORT')
    for key in ('strategy_sha256','dataset_sha256'):
        m=fixture();m[key]='G'*64;rejected(m,'INVALID_'+key.upper())
    for value in (-1,True,31536001,float('nan')):
        m=fixture();m['embargo_seconds']=value;rejected(m,'INVALID_EMBARGO')
def test_unsorted_prior_intervals_use_latest_end():
    m=fixture();m['previously_used'].append(dict(start=201,end=211))
    rejected(m,'PRIOR_INFORMATION_OVERLAP_OR_EMBARGO')
def test_holdout_before_replication_also_protected():
    m=fixture();m['reserved_holdout']=[dict(start=195,end=201)]
    rejected(m,'HOLDOUT_OVERLAP_OR_EMBARGO')
    m['reserved_holdout'][0]['end']=200
    assert AUDIT(m)['status']=='TEMPORAL_METADATA_VERIFIED_NOT_ADMITTED'
