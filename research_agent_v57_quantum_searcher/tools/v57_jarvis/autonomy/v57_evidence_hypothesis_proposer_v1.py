import hashlib
import json
from pathlib import Path

STATE = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
SOURCE = Path('/root/jarvis-migration/target-literature-scope-20261011.json')
OUTPUT = STATE / 'evidence_hypothesis_proposals_v1.json'

def main():
    agenda = json.loads((STATE / 'research_agenda_v4.json').read_text())
    literature = json.loads(SOURCE.read_text())
    assert agenda['active'] is None
    assert all(item['status'] == 'EXHAUSTED' for item in agenda['items'])
    assert literature['kind'] == 'JARVIS_TARGET_LITERATURE_SCOPE_V1'
    proposals = []
    for source in literature['sources']:
        markets = source.get('mentions_target_markets', {})
        if not source.get('abstract_available') or not source.get('abstract_sha256'):
            continue
        if not (markets.get('bitcoin') or markets.get('crypto')):
            continue
        doi = source.get('doi', '')
        if not doi:
            continue
        hypothesis_id = hashlib.sha256(('BTCUSD|LITERATURE_TRIAGE|' + doi).encode()).hexdigest()
        proposals.append({'hypothesis_id': hypothesis_id, 'market': 'BTCUSD', 'source_doi': doi, 'source_title': source.get('title'), 'evidence_source_sha256': source['abstract_sha256'], 'causal_dimension': 'UNVERIFIED_LITERATURE_MECHANISM', 'statement': 'Assess whether the cited mechanism is measurable with available BTCUSD data before formulating a directional hypothesis.', 'missing_evidence': ['FULL_TEXT_AND_METHOD_VERIFICATION', 'INDEPENDENT_REPLICATION', 'MECHANISM_TO_FEATURE_MAPPING', 'DATA_FEASIBILITY', 'NOVELTY_REVIEW'], 'status': 'REVIEW_ONLY_NOT_ADMITTED', 'orders_allowed': False, 'mt5_allowed': False, 'holdout_allowed': False, 'auto_promotion_allowed': False, 'execution_authorized': False})
    doc = {'kind': 'V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1', 'status': 'TRIAGE_ONLY', 'source_file_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'exhausted_agenda_count': len(agenda['items']), 'proposal_count': len(proposals), 'proposals': proposals, 'execution_authorized': False, 'orders_allowed': False, 'mt5_allowed': False, 'holdout_allowed': False, 'auto_promotion_allowed': False}
    assert all(not p['execution_authorized'] for p in proposals)
    temp = OUTPUT.with_suffix('.tmp')
    temp.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
    temp.replace(OUTPUT)
    print('ALL PASS|EVIDENCE_HYPOTHESIS_PROPOSER|TRIAGE=' + str(len(proposals)) + '|EXECUTION=DENIED')

if __name__ == '__main__':
    main()
