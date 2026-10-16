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


def verify_signed_initial_review(packet_path, review_path, signature_path, trust_key_path, supplemental_index_path=None):
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
        supplemental_index_sha256 = None
        if supplemental_index_path is not None:
            index_bytes = read_regular(supplemental_index_path, 16384)
            index = json.loads(index_bytes)
            original_digests = {name: item['sha256'] for name, item in evidence.items()}
            pairs = {
                'bounded_coinm_depth10_12_seconds': 'coinm_symbol_specific_l2_public_source_probe_v1.json',
                'bounded_coinm_depth10_and_forceorder_45_seconds': 'coinm_target_liquidation_channel_one_shot_v1.json',
            }
            if (not isinstance(index, dict)
                    or index.get('kind') != 'OMEGA_STAGE03_INDEPENDENT_REVIEW_HANDOFF_INDEX_V1'
                    or index.get('review_packet_sha256') != hashlib.sha256(packet_bytes).hexdigest()
                    or index.get('preexperiment_protocol_sha256') != evidence['protocol']['sha256']
                    or index.get('review_packet_verified_eight_source_digests') != original_digests
                    or index.get('source_verification', {}).get('symbol') != 'BTCUSD_PERP'
                    or index.get('source_verification', {}).get('venue') != 'BINANCE_COINM'
                    or index.get('supplemental_evidence_not_bound_to_original_packet_signature') is not True
                    or any(index.get(k) is not False for k in
                           ('independent_reviewer_signed', 'scientific_admission',
                            'development_experiment_authorized', 'orders_allowed',
                            'mt5_allowed', 'holdout_allowed', 'auto_promotion_allowed'))):
                return result('DENY_INITIAL_REVIEW_SUPPLEMENT_BINDING')
            extra = index.get('supplemental_evidence_sha256')
            if not isinstance(extra, dict) or set(extra) != set(pairs):
                return result('DENY_INITIAL_REVIEW_SUPPLEMENT_BINDING')
            for name, filename in pairs.items():
                digest = extra[name]
                if (not isinstance(digest, str) or len(digest) != 64
                        or any(c not in '0123456789abcdef' for c in digest)):
                    return result('DENY_INITIAL_REVIEW_SUPPLEMENT_BINDING')
                sample = read_regular(root / 'stage03_liquidation_source_access_v1' / filename, 50000)
                if hashlib.sha256(sample).hexdigest() != digest:
                    return result('DENY_INITIAL_REVIEW_SUPPLEMENT_TAMPERED')
            supplemental_index_sha256 = hashlib.sha256(index_bytes).hexdigest()
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError):
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
        if supplemental_index_sha256 is not None:
            expected['supplemental_review_index_sha256'] = supplemental_index_sha256
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


def verify_signed_scientific_assessment(index_path, provenance_path,
                                        review_path, signature_path, trust_key_path):
    """Verify receipt and binding of an externally signed assessment, never grant science or execution.

    Separate root-controlled authority and future-source custody are mandatory.
    The integrity of a signed statement is NOT proof that its scientific claims are true.
    """
    import os
    import stat
    import subprocess
    import tempfile

    safe = dict(scientific_admission=False, research_execution_authorized=False,
                development_experiment_authorized=False, orders_allowed=False,
                mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)

    def result(status):
        return dict(kind='OMEGA_STAGE03_SIGNED_SCIENTIFIC_ASSESSMENT_INTAKE_V1',
                    status=status, **safe)

    def read(path, max_bytes, root_owned=False):
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as fd:
            st = os.fstat(fd.fileno())
            if (not stat.S_ISREG(st.st_mode) or st.st_size <= 0
                    or st.st_size > max_bytes
                    or (root_owned and (st.st_uid != 0 or st.st_mode & 0o022))):
                raise ValueError('UNTRUSTED_OR_OVERSIZED_FILE')
            return fd.read(max_bytes + 1)

    try:
        index_bytes = read(index_path, 16384)
        index = json.loads(index_bytes)
        provenance_bytes = read(provenance_path, 16384)
        provenance = json.loads(provenance_bytes)
        if (not isinstance(index, dict)
                or index.get('kind') != 'OMEGA_STAGE03_INDEPENDENT_REVIEW_HANDOFF_INDEX_V1'
                or index.get('independent_reviewer_signed') is not False
                or index.get('scientific_admission') is not False
                or not isinstance(provenance, dict)
                or provenance.get('kind') != 'OMEGA_STAGE03_PROSPECTIVE_SOURCE_PROVENANCE_V1'
                or provenance.get('instrument') != 'BINANCE_COINM_BTCUSD_PERP'
                or provenance.get('initial_packet_sha256') != index.get('review_packet_sha256')
                or provenance.get('review_index_sha256') != hashlib.sha256(index_bytes).hexdigest()
                or provenance.get('research_execution_authorized') is not False
                or provenance.get('orders_allowed') is not False
                or provenance.get('holdout_allowed') is not False):
            return result('DENY_SCIENTIFIC_SOURCE_SCHEMA')
        sources = provenance.get('sources')
        expected = {'target_liquidation_receipts','receipt_clock_attestation',
                    'prospective_preregistration','fixed_control_protocol'}
        if not isinstance(sources, dict) or set(sources) != expected:
            return result('DENY_SCIENTIFIC_SOURCE_SCHEMA')
        folder = Path(provenance_path).parent
        used_names = set()
        for descriptor in sources.values():
            if not isinstance(descriptor, dict) or set(descriptor) != {'filename','sha256'}:
                return result('DENY_SCIENTIFIC_SOURCE_SCHEMA')
            name, sha = descriptor['filename'], descriptor['sha256']
            if name in used_names:
                return result('DENY_SCIENTIFIC_SOURCE_DUPLICATED')
            used_names.add(name)
            if (not isinstance(name, str) or Path(name).name != name
                    or name.startswith('.') or not name.endswith('.json')
                    or not isinstance(sha, str) or len(sha) != 64
                    or any(c not in '0123456789abcdef' for c in sha)):
                return result('DENY_SCIENTIFIC_SOURCE_PATH_OR_HASH')
            if hashlib.sha256(read(folder / name, 2000000)).hexdigest() != sha:
                return result('DENY_SCIENTIFIC_SOURCE_TAMPERED')
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError):
        return result('DENY_SCIENTIFIC_SOURCE_NOT_VERIFIED')

    try:
        key = read(trust_key_path, 4096, root_owned=True)
    except (OSError, ValueError):
        return result('DENY_SEPARATE_SCIENTIFIC_REVIEW_AUTHORITY_NOT_PROVISIONED')
    try:
        review_bytes = read(review_path, 16384)
        signature_bytes = read(signature_path, 256)
        review = json.loads(review_bytes)
        expected_review = {
            'kind': 'OMEGA_EXTERNAL_STAGE03_SCIENTIFIC_ASSESSMENT_V1',
            'instrument': 'BINANCE_COINM_BTCUSD_PERP',
            'review_index_sha256': hashlib.sha256(index_bytes).hexdigest(),
            'provenance_sha256': hashlib.sha256(provenance_bytes).hexdigest(),
        }
        permitted = {'REJECT_INSUFFICIENT_EVIDENCE', 'REQUEST_ADDITIONAL_EVIDENCE',
                     'ELIGIBLE_FOR_SEPARATE_SCIENTIFIC_ADMISSION_REVIEW_ONLY'}
        if (not isinstance(review, dict)
                or set(review) != set(expected_review) | {'reviewer_id','decision'}
                or any(review.get(k) != v for k, v in expected_review.items())
                or review.get('decision') not in permitted
                or not isinstance(review.get('reviewer_id'), str)
                or not review['reviewer_id'].strip()):
            return result('DENY_SCIENTIFIC_REVIEW_BINDING')
        with tempfile.TemporaryDirectory(prefix='omega-science-review-') as folder_name:
            temp = Path(folder_name)
            key_file, review_file, sig_file = (temp / n for n in ('key.pem','review.json','review.sig'))
            key_file.write_bytes(key)
            review_file.write_bytes(review_bytes)
            sig_file.write_bytes(signature_bytes)
            info = subprocess.run(['/usr/bin/openssl','pkey','-pubin','-in',str(key_file),
                                   '-text_pub','-noout'],capture_output=True,timeout=6)
            if info.returncode != 0 or b'ED25519 Public-Key' not in info.stdout:
                return result('DENY_SCIENTIFIC_REVIEW_KEY_NOT_ED25519')
            check = subprocess.run(['/usr/bin/openssl','pkeyutl','-verify','-pubin',
                                    '-inkey',str(key_file),'-sigfile',str(sig_file),
                                    '-rawin','-in',str(review_file)],capture_output=True,timeout=6)
        if check.returncode != 0:
            return result('DENY_SCIENTIFIC_REVIEW_SIGNATURE_INVALID')
        return result('SIGNED_SCIENTIFIC_ASSESSMENT_' + review['decision'] + '_NOT_AUTHORIZED')
    except (OSError, ValueError, TypeError, UnicodeError, subprocess.TimeoutExpired):
        return result('DENY_SCIENTIFIC_REVIEW_UNREADABLE')
