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


def verify_signed_initial_review(packet_path, review_path, signature_path, trust_key_path):
    """Validate independent *initial* review only. Never approve experiments or final admission.

    The externally controlled Ed25519 public key must be provisioned outside the
    repository. The signed reviewer verdict is bound to the immutable packet and
    its seven source digests; a signature alone does not establish causal novelty.
    """
    import os
    import stat
    import subprocess
    import tempfile

    safe = dict(research_execution_authorized=False, execution_authorized=False,
                independent_replication_proven=False, causal_novelty_proven=False,
                orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
                auto_promotion_allowed=False)

    def result(status):
        return dict(status=status, **safe)

    def read_regular(path, limit, trusted=False):
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as fd:
            info = os.fstat(fd.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                raise ValueError('INVALID_FILE')
            if trusted and (info.st_uid != 0 or info.st_mode & 0o022):
                raise ValueError('UNTRUSTED_EXTERNAL_AUTHORITY')
            value = fd.read(limit + 1)
            if len(value) > limit:
                raise ValueError('FILE_TOO_LARGE')
            return value

    try:
        packet_bytes = read_regular(packet_path, 32768)
        packet = json.loads(packet_bytes)
        if (not isinstance(packet, dict)
                or packet.get('kind') != 'OMEGA_STAGE03_EXTERNAL_PREEXPERIMENT_REVIEW_HANDOFF_V1'
                or packet.get('status') != 'READY_FOR_EXTERNAL_REVIEW_ONLY'
                or packet.get('instrument') != 'BINANCE_COINM_BTCUSD_PERP'
                or any(packet.get(k) is not False for k in
                       ('development_authorized', 'candidate_admitted', 'search_executed',
                        'backtest_executed', 'orders_allowed', 'mt5_allowed',
                        'holdout_allowed', 'auto_promotion_allowed'))):
            return result('DENY_INITIAL_REVIEW_PACKET_SCHEMA')
        evidence = packet.get('verified_source_files')
        required = {'protocol', 'review', 'regimes', 'temporal', 'costs', 'live', 'other_market'}
        allowed = required | {'historical_quotes'}
        if not isinstance(evidence, dict) or not required.issubset(evidence) or set(evidence) - allowed:
            return result('DENY_INITIAL_REVIEW_EVIDENCE_SCHEMA')
        proposed = packet.get('development_protocol_proposal_for_independent_review')
        if proposed is not None:
            decisions = proposed.get('independent_reviewer_can_choose') if isinstance(proposed, dict) else None
            permitted = {'ELIGIBLE_FOR_SCIENTIFIC_INITIAL_REVIEW_ONLY',
                         'REJECT_REDUNDANT_MECHANISM', 'REJECT_INSUFFICIENT_SOURCE',
                         'REQUEST_FIXED_DEFINITION'}
            if (not isinstance(decisions, list) or len(decisions) != len(permitted)
                    or any(not isinstance(x, str) for x in decisions)
                    or set(decisions) != permitted):
                return result('DENY_INITIAL_REVIEW_PACKET_DECISION_MISMATCH')
        root = Path(packet_path).parent.parent
        for entry in evidence.values():
            if not isinstance(entry, dict) or set(entry) != {'relative_file', 'sha256'}:
                return result('DENY_INITIAL_REVIEW_EVIDENCE_SCHEMA')
            parts = Path(entry['relative_file']).parts if isinstance(entry['relative_file'], str) else ()
            if not parts or parts[0] != 'stage03_liquidation_source_access_v1' or '..' in parts:
                return result('DENY_INITIAL_REVIEW_PATH')
            sha = entry['sha256']
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                return result('DENY_INITIAL_REVIEW_HASH')
            raw = read_regular(root.joinpath(*parts), 50000)
            if hashlib.sha256(raw).hexdigest() != sha:
                return result('DENY_INITIAL_REVIEW_EVIDENCE_TAMPERED')
        if hashlib.sha256(read_regular(root / evidence['protocol']['relative_file'], 16384)).hexdigest() != evidence['protocol']['sha256']:
            return result('DENY_INITIAL_REVIEW_PROTOCOL_HASH')
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return result('DENY_INITIAL_REVIEW_PACKET_UNREADABLE')

    try:
        key = read_regular(trust_key_path, 4096, trusted=True)
    except (OSError, ValueError):
        return result('DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED')
    try:
        review_bytes = read_regular(review_path, 16384)
        signature_bytes = read_regular(signature_path, 256)
        payload = json.loads(review_bytes)
        expected = {
            'kind': 'OMEGA_EXTERNAL_INITIAL_SCIENTIFIC_REVIEW_V1',
            'packet_sha256': hashlib.sha256(packet_bytes).hexdigest(),
            'protocol_sha256': evidence['protocol']['sha256'],
            'instrument': 'BINANCE_COINM_BTCUSD_PERP',
        }
        allowed_decisions = {
            'ELIGIBLE_FOR_SCIENTIFIC_INITIAL_REVIEW_ONLY',
            'REJECT_REDUNDANT_MECHANISM',
            'REJECT_INSUFFICIENT_SOURCE',
            'REQUEST_FIXED_DEFINITION',
        }
        if (not isinstance(payload, dict) or any(payload.get(k) != v for k, v in expected.items())
                or payload.get('decision') not in allowed_decisions):
            return result('DENY_INITIAL_REVIEW_SIGNATURE_BINDING')
        if not isinstance(payload.get('reviewer_id'), str) or not payload['reviewer_id'].strip():
            return result('DENY_INITIAL_REVIEW_REVIEWER_ID')
        with tempfile.TemporaryDirectory(prefix='omega-initial-review-') as temp:
            keypath = Path(temp) / 'pub.pem'
            reviewpath = Path(temp) / 'review.json'
            sigpath = Path(temp) / 'review.sig'
            keypath.write_bytes(key)
            reviewpath.write_bytes(review_bytes)
            sigpath.write_bytes(signature_bytes)
            info = subprocess.run(['/usr/bin/openssl','pkey','-pubin','-in',str(keypath),
                                   '-text_pub','-noout'],capture_output=True,timeout=6)
            if info.returncode != 0 or b'ED25519 Public-Key' not in info.stdout:
                return result('DENY_INITIAL_REVIEW_KEY_NOT_ED25519')
            check = subprocess.run(['/usr/bin/openssl','pkeyutl','-verify','-pubin',
                                    '-inkey',str(keypath),'-sigfile',str(sigpath),
                                    '-rawin','-in',str(reviewpath)],capture_output=True,timeout=6)
        if check.returncode != 0:
            return result('DENY_INITIAL_REVIEW_SIGNATURE_INVALID')
        if payload['decision'] == 'ELIGIBLE_FOR_SCIENTIFIC_INITIAL_REVIEW_ONLY':
            return result('INITIAL_REVIEW_SIGNATURE_VERIFIED_NOT_AUTHORIZED')
        return result('SIGNED_INITIAL_REVIEW_' + payload['decision'] + '_NOT_AUTHORIZED')
    except (OSError, ValueError, TypeError, UnicodeError, subprocess.TimeoutExpired):
        return result('DENY_INITIAL_REVIEW_UNREADABLE')
