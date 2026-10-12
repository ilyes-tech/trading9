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
