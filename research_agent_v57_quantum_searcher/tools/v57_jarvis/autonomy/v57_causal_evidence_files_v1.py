"""Read-only independent-file verification; NEVER grants scientific admission."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')


def check_file(filename, expected_hash):
    if not isinstance(filename, str) or not filename.endswith('.json') or '/' in filename or '\\' in filename or filename.startswith('.'):
        return 'DENY_PATH', None
    if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(c not in '0123456789abcdef' for c in expected_hash):
        return 'DENY_HASH_FORMAT', None
    path = ROOT / filename
    if not path.is_file() or path.is_symlink():
        return 'DENY_MISSING_OR_LINK', None
    raw = path.read_bytes()
    if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != expected_hash:
        return 'DENY_HASH_OR_SIZE', None
    try:
        doc = json.loads(raw)
    except (ValueError, UnicodeError):
        return 'DENY_JSON', None
    if not isinstance(doc, dict):
        return 'DENY_SCHEMA', None
    if any(doc.get(k) is not False for k in ('orders_allowed', 'mt5_allowed', 'holdout_allowed', 'auto_promotion_allowed')):
        return 'DENY_UNSAFE', None
    return 'FILE_INTEGRITY_VERIFIED', doc


def assess(candidate):
    if not isinstance(candidate, dict):
        return 'DENY_MALFORMED'
    a, adoc = check_file(candidate.get('novelty_file'), candidate.get('novelty_sha256'))
    if a != 'FILE_INTEGRITY_VERIFIED':
        return 'NOVELTY_' + a
    b, bdoc = check_file(candidate.get('replication_file'), candidate.get('replication_sha256'))
    if b != 'FILE_INTEGRITY_VERIFIED':
        return 'REPLICATION_' + b
    if candidate['novelty_file'] == candidate['replication_file'] or candidate['novelty_sha256'] == candidate['replication_sha256']:
        return 'DENY_IDENTICAL_FILES'
    if adoc.get('kind') != 'V57_CAUSAL_NOVELTY_EVIDENCE' or bdoc.get('kind') != 'V57_CAUSAL_REPLICATION_EVIDENCE':
        return 'DENY_EVIDENCE_TYPES'
    if not isinstance(candidate.get('family'), str) or not candidate['family'].strip():
        return 'DENY_FAMILY'
    if adoc.get('family') != candidate['family'] or bdoc.get('family') != candidate['family']:
        return 'DENY_FAMILY_MISMATCH'
    return 'FILES_INTEGRITY_VERIFIED_CAUSAL_VALIDATION_PENDING'


def main():
    tests = [
        ({}, 'NOVELTY_DENY_PATH'),
        ({'novelty_file': '../outside.json'}, 'NOVELTY_DENY_PATH'),
        ({'novelty_file': 'missing.json', 'novelty_sha256': '0'*64}, 'NOVELTY_DENY_MISSING_OR_LINK'),
        ({'novelty_file': 'multimarket_evidence_registry_v3.json', 'novelty_sha256': 'bad'}, 'NOVELTY_DENY_HASH_FORMAT'),
    ]
    for candidate, expected in tests:
        actual = assess(candidate)
        if actual != expected:
            raise RuntimeError('TEST_FAILURE:' + expected + ':' + actual)
    print('ALL PASS|CAUSAL_EVIDENCE_FILES_V1|NEGATIVE_TESTS=4|READ_ONLY|ADMISSION=NO')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('STOP|FAIL|CAUSAL_EVIDENCE_FILES_V1|' + str(error))
        sys.exit(3)
