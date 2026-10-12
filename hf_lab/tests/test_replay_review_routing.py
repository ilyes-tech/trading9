"""Bounded pending-review routing; all files are temporary synthetic fixtures."""
import hashlib,json,os,runpy
from pathlib import Path
import pytest
ROOT=Path('/home/trading/TradingAI-HF-Lab')
A=ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy'
MODULE=os.environ.get('OMEGA_ROUTING_VERIFIER',str(A/'v57_independent_evidence_verifier_v2.py'))
SAFE=dict(orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
@pytest.fixture
def reviewer(tmp_path):
    ns=runpy.run_path(MODULE);f=ns['review_pending_replay'];f.__globals__['S']=tmp_path
    return f,tmp_path
def write_request(p,**changes):
    d=dict(kind='V57_REPLAY_REVIEW_REQUEST_V1',evidence_file='bundle.json',evidence_sha256='0'*64,
           strategy_sha256='a'*64,dataset_sha256='b'*64,**SAFE);d.update(changes)
    (p/'replay_review_request_v1.json').write_text(json.dumps(d))
def test_absent_request_is_missing(reviewer):
    f,p=reviewer;assert f()['status']=='MISSING_REPLAY_EVIDENCE'
def test_bad_path_link_size_and_json_rejected(reviewer):
    f,p=reviewer
    write_request(p,evidence_file='../outside.json');assert f()['reason']=='INVALID_PATH'
    write_request(p);(p/'bundle.json').symlink_to('/nonexistent')
    assert f()['status']=='REPLAY_REVIEW_INPUT_REJECTED'
    (p/'bundle.json').unlink();(p/'bundle.json').write_bytes(b' '*2000001)
    assert f()['reason']=='FILE_SIZE_LIMIT'
    (p/'replay_review_request_v1.json').write_text('[]')
    assert f()['reason']=='INVALID_SCHEMA'
    (p/'replay_review_request_v1.json').write_bytes(b' '*16385)
    assert f()['reason']=='FILE_SIZE_LIMIT'
def test_hash_and_unsafe_flags_fail(reviewer):
    f,p=reviewer;write_request(p)
    (p/'bundle.json').write_text(json.dumps(dict(kind='V57_REPLAY_REVIEW_BUNDLE_V1',**SAFE)))
    assert f()['reason']=='EVIDENCE_HASH_MISMATCH'
    write_request(p,orders_allowed=True);assert f()['reason']=='UNSAFE_FLAGS'
def test_real_composed_evaluation_is_used(reviewer):
    f,p=reviewer
    helpers=runpy.run_path(str(ROOT/'hf_lab/tests/test_composed_replay_evidence.py'))
    folds,settings,manifest=helpers['fixture']()
    def save():
        raw=json.dumps(dict(kind='V57_REPLAY_REVIEW_BUNDLE_V1',folds=folds,settings=settings,manifest=manifest,**SAFE)).encode()
        (p/'bundle.json').write_bytes(raw);write_request(p,evidence_sha256=hashlib.sha256(raw).hexdigest())
    save();out=f()
    assert out['status']=='REPLAY_CHECKS_PASS_SCIENTIFIC_REVIEW_BLOCKED'
    assert out['request_authenticity_verified'] is False and out['new_research_authorized'] is False
    folds[0][0]['net_r']=123;save()
    assert f()['reason']=='MISMATCH_NET_R'
    manifest['dataset_sha256']='c'*64;save()
    assert f()['reason']=='MANIFEST_BINDING_MISMATCH'
def test_gate_diagnostic_cannot_authorize(tmp_path):
    gate=Path(os.environ.get('OMEGA_ROUTING_GATE',str(A/'v57_search_authorization_gate_v1.py')))
    ns=runpy.run_path(str(gate));main=ns['main'];main.__globals__['S']=tmp_path
    (tmp_path/'independent_evidence_verifier_v2.json').write_text(json.dumps(dict(replay_review=dict(status='REPLAY_CHECKS_PASS_SCIENTIFIC_REVIEW_BLOCKED'))))
    assert main()==3
    out=json.loads((tmp_path/'search_authorization_v1.json').read_text())
    assert out['authorized'] is False and out['max_candidates']==0
    assert out['replay_review_status']=='REPLAY_CHECKS_PASS_SCIENTIFIC_REVIEW_BLOCKED'
