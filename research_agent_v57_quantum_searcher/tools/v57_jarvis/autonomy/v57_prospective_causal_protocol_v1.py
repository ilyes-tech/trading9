"""Preregister or submit a review-only scientific protocol; never inspect holdout or trade."""
import hashlib
import json
import sys
from pathlib import Path

S = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
SAFE = dict(orders_allowed=False, mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)
ORDER = ['hypothesis', 'source_audit', 'preregister', 'development_only',
         'independent_replication', 'scientific_review']
REQUIRED_HYPOTHESIS = (
    'statement', 'market', 'mechanism', 'observable_signal', 'outcome',
    'falsification_rule', 'data_provenance', 'information_timing',
    'development_window', 'cost_model', 'independent_review_plan',
)
BASE = dict(schema_version=1, kind='V57_PROSPECTIVE_CAUSAL_PROTOCOL_V1',
            hypothesis_status='UNFORMULATED', evidence_status='MISSING',
            validation_order=ORDER, minimum_boot_mean_positive_probability=0.90,
            minimum_boot_pf_ge1_probability=0.80, minimum_positive_half_segments=4,
            maximum_trade_profit_share=0.35, maximum_day_profit_share=0.50,
            data_separation='CHRONOLOGICAL_NO_OVERLAP_NO_HOLDOUT_ACCESS',
            execution_authorized=False, **SAFE)


def validate(protocol):
    if not isinstance(protocol, dict):
        return 'DENY_MALFORMED'
    if protocol.get('kind') != BASE['kind'] or protocol.get('schema_version') != 1:
        return 'DENY_SCHEMA'
    if set(protocol) - (set(BASE) | {'hypothesis'}):
        return 'DENY_UNKNOWN_FIELDS'
    if any(protocol.get(k) is not False for k in (*SAFE, 'execution_authorized')):
        return 'DENY_UNSAFE'
    if protocol.get('evidence_status') != 'MISSING':
        return 'DENY_PRETEND_EVIDENCE'
    if protocol.get('validation_order') != ORDER:
        return 'DENY_ORDER'
    if protocol.get('minimum_boot_mean_positive_probability') != 0.90:
        return 'DENY_WEAK_THRESHOLD'
    if protocol.get('minimum_boot_pf_ge1_probability') != 0.80:
        return 'DENY_WEAK_THRESHOLD'
    if protocol.get('minimum_positive_half_segments') != 4:
        return 'DENY_WEAK_THRESHOLD'
    if protocol.get('maximum_trade_profit_share') != 0.35 or protocol.get('maximum_day_profit_share') != 0.50:
        return 'DENY_WEAK_CONCENTRATION'
    if protocol.get('data_separation') != 'CHRONOLOGICAL_NO_OVERLAP_NO_HOLDOUT_ACCESS':
        return 'DENY_LEAKAGE_RISK'
    status = protocol.get('hypothesis_status')
    if status == 'UNFORMULATED':
        return 'DENY_PRETEND_EVIDENCE' if protocol.get('hypothesis') is not None else 'PROTOCOL_VALID_NOT_AUTHORIZED'
    if status != 'FORMULATED_FOR_REVIEW':
        return 'DENY_PRETEND_EVIDENCE'
    h = protocol.get('hypothesis')
    if not isinstance(h, dict) or set(h) != set(REQUIRED_HYPOTHESIS):
        return 'DENY_INCOMPLETE_HYPOTHESIS'
    if any(not isinstance(h[k], str) or not h[k].strip() or len(h[k]) > 2000 for k in REQUIRED_HYPOTHESIS):
        return 'DENY_INCOMPLETE_HYPOTHESIS'
    return 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'


def atomic_json(path, payload):
    S.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + '\n')
    tmp.replace(path)


def review_file(path):
    # A review request is NOT a scientific approval. Never modify the base protocol.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
        raise ValueError('INVALID_REVIEW_FILE')
    raw = path.read_bytes()
    try:
        proposal = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('INVALID_REVIEW_JSON') from error
    verdict = validate(proposal)
    report = dict(schema_version=1, kind='V57_PROSPECTIVE_CAUSAL_PROTOCOL_REVIEW_V1',
                  status=verdict, submission_sha256=hashlib.sha256(raw).hexdigest(),
                  hypothesis_formulated=verdict == 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED',
                  independent_evidence_verified=False,
                  research_execution_authorized=False, execution_authorized=False,
                  **SAFE)
    atomic_json(S / 'prospective_causal_protocol_review_v1.json', report)
    print(('ALL PASS' if report['hypothesis_formulated'] else 'STOP|FAIL')
          + '|PROTOCOL_REVIEW_V1|' + verdict + '|EXECUTION=NO')
    return 0 if report['hypothesis_formulated'] else 3


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--review-file':
        return review_file(Path(sys.argv[2]))
    if len(sys.argv) != 1:
        raise ValueError('USAGE: [--review-file JSON_PATH]')
    p = dict(BASE)
    cases = [
        (p, 'PROTOCOL_VALID_NOT_AUTHORIZED'),
        (dict(p, holdout_allowed=True), 'DENY_UNSAFE'),
        (dict(p, execution_authorized=True), 'DENY_UNSAFE'),
        (dict(p, evidence_status='VERIFIED'), 'DENY_PRETEND_EVIDENCE'),
        (dict(p, minimum_boot_mean_positive_probability=0.50), 'DENY_WEAK_THRESHOLD'),
        (dict(p, data_separation='UNKNOWN'), 'DENY_LEAKAGE_RISK'),
    ]
    for case, expected in cases:
        if validate(case) != expected:
            raise RuntimeError('PROTOCOL_TEST:' + expected)
    atomic_json(S / 'prospective_causal_protocol_v1.json', p)
    print('ALL PASS|PROSPECTIVE_CAUSAL_PROTOCOL_V1|TESTS=6|PREREGISTRATION_ONLY|EXECUTION=NO')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print('STOP|FAIL|PROSPECTIVE_CAUSAL_PROTOCOL_V1|' + str(error))
        sys.exit(3)
