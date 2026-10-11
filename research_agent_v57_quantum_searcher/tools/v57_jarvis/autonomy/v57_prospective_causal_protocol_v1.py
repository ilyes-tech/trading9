"""Preregister a fail-closed scientific protocol; never inspect holdout or trade."""
import hashlib
import json
import sys
from pathlib import Path

S = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
SAFE = dict(orders_allowed=False, mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)


def validate(protocol):
    if not isinstance(protocol, dict):
        return 'DENY_MALFORMED'
    if any(protocol.get(k) is not False for k in SAFE):
        return 'DENY_UNSAFE'
    if protocol.get('hypothesis_status') != 'UNFORMULATED' or protocol.get('evidence_status') != 'MISSING':
        return 'DENY_PRETEND_EVIDENCE'
    if protocol.get('validation_order') != ['hypothesis', 'source_audit', 'preregister', 'development_only', 'independent_replication', 'scientific_review']:
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
    return 'PROTOCOL_VALID_NOT_AUTHORIZED'


def main():
    p = dict(schema_version=1, kind='V57_PROSPECTIVE_CAUSAL_PROTOCOL_V1',
             hypothesis_status='UNFORMULATED', evidence_status='MISSING',
             validation_order=['hypothesis', 'source_audit', 'preregister', 'development_only', 'independent_replication', 'scientific_review'],
             minimum_boot_mean_positive_probability=0.90,
             minimum_boot_pf_ge1_probability=0.80, minimum_positive_half_segments=4,
             maximum_trade_profit_share=0.35, maximum_day_profit_share=0.50,
             data_separation='CHRONOLOGICAL_NO_OVERLAP_NO_HOLDOUT_ACCESS',
             execution_authorized=False, **SAFE)
    cases = [(p, 'PROTOCOL_VALID_NOT_AUTHORIZED'),
             (dict(p, holdout_allowed=True), 'DENY_UNSAFE'),
             (dict(p, evidence_status='VERIFIED'), 'DENY_PRETEND_EVIDENCE'),
             (dict(p, minimum_boot_mean_positive_probability=0.50), 'DENY_WEAK_THRESHOLD'),
             (dict(p, data_separation='UNKNOWN'), 'DENY_LEAKAGE_RISK')]
    for case, expected in cases:
        if validate(case) != expected:
            raise RuntimeError('PROTOCOL_TEST:' + expected)
    raw = json.dumps(p, indent=2, sort_keys=True) + '\n'
    dest = S / 'prospective_causal_protocol_v1.json'
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(raw)
    tmp.replace(dest)
    print('ALL PASS|PROSPECTIVE_CAUSAL_PROTOCOL_V1|TESTS=5|PREREGISTRATION_ONLY|EXECUTION=NO')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('STOP|FAIL|PROSPECTIVE_CAUSAL_PROTOCOL_V1|' + str(error))
        sys.exit(3)
