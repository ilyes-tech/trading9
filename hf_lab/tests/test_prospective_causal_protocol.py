"""Fail-closed tests of review-only hypothesis submission; no live search or trading."""
import json
import runpy
from pathlib import Path

A = Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
NS = runpy.run_path(str(A / 'v57_prospective_causal_protocol_v1.py'))
BASE = NS['BASE']
validate = NS['validate']
FIELDS = NS['REQUIRED_HYPOTHESIS']


def complete():
    return dict(BASE, hypothesis_status='FORMULATED_FOR_REVIEW',
                hypothesis={key: 'synthetic-test-only' for key in FIELDS})


def test_existing_unformulated_protocol_stays_valid_but_not_authorized():
    assert validate(dict(BASE)) == 'PROTOCOL_VALID_NOT_AUTHORIZED'
    assert validate(dict(BASE, hypothesis_status='ADMITTED')) == 'DENY_PRETEND_EVIDENCE'


def test_complete_hypothesis_is_reviewable_not_authorized():
    p = complete()
    assert p['execution_authorized'] is False
    assert validate(p) == 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'


def test_incomplete_or_false_evidence_cannot_pass():
    p = complete()
    p['hypothesis'].pop('falsification_rule')
    assert validate(p) == 'DENY_INCOMPLETE_HYPOTHESIS'
    p = complete()
    p['hypothesis']['mechanism'] = ' '
    assert validate(p) == 'DENY_INCOMPLETE_HYPOTHESIS'
    p = complete()
    p['evidence_status'] = 'VERIFIED'
    assert validate(p) == 'DENY_PRETEND_EVIDENCE'


def test_safety_and_validation_rules_stay_closed():
    for change in (
        {'orders_allowed': True}, {'execution_authorized': True},
        {'holdout_allowed': True}, {'mt5_allowed': True},
        {'research_execution_authorized': True},
        {'data_separation': 'UNKNOWN'},
    ):
        actual = validate(dict(complete(), **change))
        assert actual.startswith('DENY_'), (change, actual)


def test_review_file_reports_only_reviewability(tmp_path):
    review = NS['review_file']
    review.__globals__['S'] = tmp_path
    base = tmp_path / 'prospective_causal_protocol_v1.json'
    base.write_text('keep-existing-base-unchanged')
    source = tmp_path / 'submission.json'
    source.write_text(json.dumps(complete()))
    assert review(source) == 0
    output = json.loads((tmp_path / 'prospective_causal_protocol_review_v1.json').read_text())
    assert output['status'] == 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'
    assert output['hypothesis_formulated'] is True
    assert output['research_execution_authorized'] is False
    assert output['orders_allowed'] is False
    assert base.read_text() == 'keep-existing-base-unchanged'


def test_review_file_rejects_symlink_and_oversize(tmp_path):
    review = NS['review_file']
    review.__globals__['S'] = tmp_path
    target = tmp_path / 'source.json'
    target.write_text(json.dumps(complete()))
    link = tmp_path / 'link.json'
    link.symlink_to(target)
    for item in (link,):
        try:
            review(item)
        except ValueError as e:
            assert str(e) == 'INVALID_REVIEW_FILE'
        else:
            assert False, 'review must reject symlinks'
    target.write_text(' ' * 16385)
    try:
        review(target)
    except ValueError as e:
        assert str(e) == 'INVALID_REVIEW_FILE'
    else:
        assert False, 'review must reject oversized inputs'


def test_stage03_preexperiment_review_is_separate_from_replication(tmp_path):
    """Review of a first experiment never needs fabricated replication evidence."""
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['first_experiment_review_status']
    gate.__globals__['PREEXPERIMENT'] = tmp_path / 'preexperiment.json'
    gate.__globals__['PREEXPERIMENT_REVIEW'] = tmp_path / 'review.json'
    assert gate() is None
    proposal = complete()
    proposal['hypothesis']['market'] = 'Binance COIN-M BTCUSD_PERP'
    raw = json.dumps(proposal).encode()
    (tmp_path / 'preexperiment.json').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (tmp_path / 'review.json').write_text(json.dumps({
        'status': 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED',
        'submission_sha256': digest,
        'independent_evidence_verified': False,
        'research_execution_authorized': False,
        'execution_authorized': False,
        'orders_allowed': False, 'mt5_allowed': False,
        'holdout_allowed': False, 'auto_promotion_allowed': False}))
    assert gate() == digest
    proposal['hypothesis']['market'] = 'different-market'
    (tmp_path / 'preexperiment.json').write_text(json.dumps(proposal))
    assert gate() is None


def test_stage03_preexperiment_rejects_unsafe_and_tampered_review(tmp_path):
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['first_experiment_review_status']
    gate.__globals__['PREEXPERIMENT'] = tmp_path / 'preexperiment.json'
    gate.__globals__['PREEXPERIMENT_REVIEW'] = tmp_path / 'review.json'
    proposal = complete()
    proposal['hypothesis']['market'] = 'BTCUSD_PERP'
    proposal_raw = json.dumps(proposal).encode()
    (tmp_path / 'preexperiment.json').write_bytes(proposal_raw)
    review = dict(status='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED',
                  submission_sha256=hashlib.sha256(proposal_raw).hexdigest(),
                  independent_evidence_verified=False,
                  research_execution_authorized=False,
                  execution_authorized=False, orders_allowed=False,
                  mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate()
    review['research_execution_authorized'] = True
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate() is None
    review['research_execution_authorized'] = False
    review['submission_sha256'] = '0' * 64
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate() is None
    (tmp_path / 'preexperiment.json').unlink()
    (tmp_path / 'preexperiment.json').symlink_to(tmp_path / 'review.json')
    assert gate() is None


def test_stage03_public_source_status_is_provisional_and_fail_closed(tmp_path):
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['public_liquidation_source_status']
    path = tmp_path / 'source.json'
    gate.__globals__['SOURCE'] = path
    assert gate() is None
    doc = dict(kind='OMEGA_STAGE03_LIQUIDATION_PUBLIC_SOURCE_ACCESS_REVIEW_V1',
               status='PUBLIC_FUTURES_INSTRUMENT_AND_BOOK_REST_ACCESS_VERIFIED_LIQUIDATION_STREAM_UNTESTED',
               instrument=dict(symbol='BTCUSD_PERP', pair='BTCUSD'),
               research_execution_authorized=False, candidate_admitted=False,
               orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
               auto_promotion_allowed=False)
    raw = json.dumps(doc).encode()
    path.write_bytes(raw)
    assert gate() == hashlib.sha256(raw).hexdigest()
    doc['orders_allowed'] = True
    path.write_text(json.dumps(doc))
    assert gate() is None
    path.unlink()
    path.symlink_to('/nonexistent')
    assert gate() is None
