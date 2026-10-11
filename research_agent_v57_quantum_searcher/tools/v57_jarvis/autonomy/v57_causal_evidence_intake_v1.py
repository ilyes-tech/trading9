"""Fail-closed, read-only intake for genuinely new causal evidence.
This tool NEVER authorizes research or trading. It reports review eligibility only.
"""
import hashlib
import json
import sys
from pathlib import Path

S = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
SAFE = ('orders_allowed', 'mt5_allowed', 'holdout_allowed', 'auto_promotion_allowed')
HEX = set('0123456789abcdef')


def assess(candidate, coverage, registry):
    if not isinstance(candidate, dict):
        return 'DENY_MALFORMED'
    family = candidate.get('native_family')
    if not isinstance(family, str) or not family.strip():
        return 'DENY_NO_FAMILY'
    if family in coverage['native_families'] or family in coverage['exhausted_families']:
        return 'DENY_EXISTING_OR_EXHAUSTED_FAMILY'
    if any(candidate.get(k) is not False for k in SAFE):
        return 'DENY_UNSAFE'
    if candidate.get('new_causal_evidence_verified') is True:
        return 'DENY_SELF_ATTESTATION'
    if candidate.get('market') not in registry['markets']:
        return 'DENY_UNKNOWN_MARKET'
    for key in ('source_sha256', 'novelty_evidence_sha256', 'independent_replication_sha256'):
        value = candidate.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in HEX for c in value):
            return 'DENY_MISSING_PROVENANCE'
    if len({candidate[k] for k in ('source_sha256', 'novelty_evidence_sha256', 'independent_replication_sha256')}) != 3:
        return 'DENY_NONINDEPENDENT_HASHES'
    return 'PENDING_INDEPENDENT_REPLICATION_REVIEW_NOT_AUTHORIZED'


def main():
    c = json.loads((S / 'native_capability_coverage_v2.json').read_text())
    r = json.loads((S / 'multimarket_evidence_registry_v3.json').read_text())
    if c.get('kind') != 'V57_NATIVE_CAPABILITY_COVERAGE_V2' or c.get('status') != 'PASS':
        raise RuntimeError('COVERAGE_INVALID')
    if r.get('kind') != 'V57_MULTIMARKET_EVIDENCE_REGISTRY_V3' or r.get('status') != 'PASS':
        raise RuntimeError('REGISTRY_INVALID')
    safe = {k: False for k in SAFE}
    valid = dict(safe, native_family='new_testable_family', market='XAUUSD', source_sha256='a'*64,
                 novelty_evidence_sha256='b'*64, independent_replication_sha256='c'*64)
    cases = [({}, 'DENY_NO_FAMILY'),
             (dict(valid, native_family='volume'), 'DENY_EXISTING_OR_EXHAUSTED_FAMILY'),
             (dict(valid, orders_allowed=True), 'DENY_UNSAFE'),
             (dict(valid, new_causal_evidence_verified=True), 'DENY_SELF_ATTESTATION'),
             (dict(valid, market='FAKE'), 'DENY_UNKNOWN_MARKET'),
             (dict(valid, source_sha256='bad'), 'DENY_MISSING_PROVENANCE'),
             (dict(valid, independent_replication_sha256='a'*64), 'DENY_NONINDEPENDENT_HASHES'),
             (valid, 'PENDING_INDEPENDENT_REPLICATION_REVIEW_NOT_AUTHORIZED')]
    for item, expected in cases:
        actual = assess(item, c, r)
        if actual != expected:
            raise RuntimeError('TEST_FAILURE:' + expected + ':' + actual)
    report = dict(schema_version=1, kind='V57_CAUSAL_EVIDENCE_INTAKE_V1', status='PASS',
                  tests=len(cases), evidence_supplied=False, novelty_proven=False,
                  research_execution_authorized=False, decision='AWAIT_INDEPENDENT_REPLICATION',
                  coverage_sha256=hashlib.sha256((S / 'native_capability_coverage_v2.json').read_bytes()).hexdigest(),
                  registry_sha256=hashlib.sha256((S / 'multimarket_evidence_registry_v3.json').read_bytes()).hexdigest(),
                  **safe)
    dest = S / 'causal_evidence_intake_v1.json'
    temp = dest.with_suffix('.tmp')
    temp.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    temp.replace(dest)
    print('ALL PASS|CAUSAL_EVIDENCE_INTAKE_V1|TESTS=8|REVIEW_ONLY|EXECUTION=NO')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('STOP|FAIL|CAUSAL_EVIDENCE_INTAKE_V1|' + str(error))
        sys.exit(3)
