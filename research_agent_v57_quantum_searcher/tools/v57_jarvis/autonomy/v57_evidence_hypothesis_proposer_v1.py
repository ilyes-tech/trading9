import hashlib
import json
from pathlib import Path

STATE = Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
SOURCE = Path('/root/jarvis-migration/target-literature-scope-20261011.json')
OUTPUT = STATE / 'evidence_hypothesis_proposals_v1.json'

# Publisher pages checked 2026-10-19. Bibliography ONLY, not raw-paper
# verification, economic edge, platform fee calibration or scientific admission.
# Never modify the frozen prior BTC-only literature scope.
VOLATILITY_BACKGROUND_REFERENCES = (
    {
        'market': 'EURUSD',
        'source_doi': '10.1111/0022-1082.85732',
        'source_title': 'Deutsche Mark-Dollar Volatility: Intraday Activity Patterns, Macroeconomic Announcements, and Longer Run Dependencies',
        'publisher_url': 'https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.85732',
        'paper_instrument': 'Deutsche-mark/US-dollar FX, pre-euro',
        'data_instrument': 'EURUSD MT5 archived M1',
        'mechanism': 'intraday conditional variance periodicity, NOT directional alpha',
        'portability_issue': 'OLD_DEMUSD_NOT_CURRENT_EURUSD_AND_FIVE_MINUTE_TO_M1_MISMATCH',
    },
    {
        'market': 'XAUUSD',
        'source_doi': '10.1002/1096-9934(200103)21:3<257::AID-FUT4>3.0.CO;2-W',
        'source_title': 'What moves the gold market?',
        'publisher_url': 'https://onlinelibrary.wiley.com/doi/10.1002/1096-9934%28200103%2921%3A3%3C257%3A%3AAID-FUT4%3E3.0.CO%3B2-W',
        'paper_instrument': 'COMEX gold futures historical sample',
        'data_instrument': 'XAUUSD MT5 archived M1',
        'mechanism': 'intraday conditional variance and macro-announcement sensitivity, NOT directional alpha',
        'portability_issue': 'COMEX_FUTURES_NOT_CURRENT_MT5_SPOT_OR_CFD_GOLD',
    },
)


def historical_volatility_background():
    """Publisher bibliographic context only; always pending mechanism review."""
    ideas=[]
    for source in VOLATILITY_BACKGROUND_REFERENCES:
        if not all(isinstance(source.get(k),str) and source[k]
                   for k in ('market','source_doi','source_title','publisher_url',
                             'paper_instrument','data_instrument','mechanism','portability_issue')):
            raise ValueError('INVALID_PUBLISHER_BACKGROUND_REFERENCE')
        market=source['market']
        if market not in ('EURUSD','XAUUSD'):
            raise ValueError('UNEXPECTED_PUBLISHER_REFERENCE_MARKET')
        identity=hashlib.sha256((market+'|BACKGROUND_VOLATILITY_LITERATURE|'+source['source_doi']).encode()).hexdigest()
        evidence=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ideas.append({
            'hypothesis_id':identity,'market':market,
            'source_doi':source['source_doi'],'source_title':source['source_title'],
            'publisher_url':source['publisher_url'],
            'source_fingerprint_type':'LOCAL_BIBLIOGRAPHIC_METADATA_NOT_INDEPENDENT_TEXT_ATTESTATION',
            'evidence_source_sha256':evidence,
            'causal_dimension':'VOLATILITY_BACKGROUND_ONLY_NOT_DIRECTIONAL_EDGE',
            'bibliographic_role':'PUBLISHER_ABSTRACT_VOLATILITY_CONTEXT_ONLY',
            'paper_instrument':source['paper_instrument'],
            'data_instrument':source['data_instrument'],
            'mechanism':source['mechanism'],
            'portability_issue':source['portability_issue'],
            'statement':'Review whether a price-only conditional-volatility question can be pre-registered for this specific current instrument; do not infer a directional strategy.',
            'missing_evidence':['PAPER_METHOD_AND_PARAMETER_SCOPE_VERIFICATION',
                                'INSTRUMENT_TRANSFER_AND_TIMEFRAME_COMPATIBILITY',
                                'INDEPENDENT_REPLICATION','DIRECTIONAL_TRADING_EDGE_UNPROVEN',
                                'CURRENT_BROKER_FEES_SPREAD_AND_FILLS_UNVERIFIED',
                                'SCIENTIFIC_ADMISSION_AND_UNTOUCHED_HOLDOUT_REQUIRED'],
            'status':'PUBLISHER_BIBLIOGRAPHY_REVIEW_ONLY_NOT_ADMITTED',
            'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,
            'auto_promotion_allowed':False,'execution_authorized':False,
        })
    return ideas


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
    proposals.extend(historical_volatility_background())
    assert len({p['hypothesis_id'] for p in proposals})==len(proposals)
    doc = {'kind': 'V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1', 'status': 'TRIAGE_ONLY', 'source_file_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'exhausted_agenda_count': len(agenda['items']), 'proposal_count': len(proposals), 'publisher_bibliography_context_count': 2, 'publisher_context_is_scientific_admission': False, 'proposals': proposals, 'execution_authorized': False, 'orders_allowed': False, 'mt5_allowed': False, 'holdout_allowed': False, 'auto_promotion_allowed': False}
    assert all(not p['execution_authorized'] for p in proposals)
    temp = OUTPUT.with_suffix('.tmp')
    temp.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
    temp.replace(OUTPUT)
    print('ALL PASS|EVIDENCE_HYPOTHESIS_PROPOSER|TRIAGE=' + str(len(proposals)) + '|EXECUTION=DENIED')

if __name__ == '__main__':
    main()
