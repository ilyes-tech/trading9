import hashlib
import json
import runpy
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
P=S/'evidence_hypothesis_proposals_v1.json'
D=Path('/root/jarvis-migration/btc-m1-data-feasibility-20261011.json')
O=S/'hypothesis_feasibility_triage_v1.json'
SOURCE=S/'stage03_liquidation_source_access_v1/one_source_review_v1.json'
PREEXPERIMENT=S/'stage03_liquidation_source_access_v1/first_experiment_protocol_review_only_v1.json'
PREEXPERIMENT_REVIEW=S/'stage03_liquidation_source_access_v1/prospective_causal_protocol_review_v1.json'
GLOBAL_FORCEORDER=S/'stage03_liquidation_source_access_v1/global_forceorder_market_type_triage_v1.json'


def non_target_liquidation_sample_sha256():
    """Record only observed USD-M payload metadata; never grant BTCUSD_PERP access."""
    try:
        if not GLOBAL_FORCEORDER.is_file() or GLOBAL_FORCEORDER.is_symlink() or GLOBAL_FORCEORDER.stat().st_size>16384:
            return None
        raw=GLOBAL_FORCEORDER.read_bytes()
        doc=json.loads(raw)
        sample=doc.get('public_observed_message_metadata')
        if (doc.get('kind')!='OMEGA_STAGE03_GLOBAL_BINANCE_LIQUIDATION_MESSAGE_SCHEMA_TRIAGE_V1'
                or doc.get('status')!='PUBLIC_REAL_FORCEORDER_MESSAGES_OBSERVED_USDM_ONLY_NO_COINM_TARGET'
                or doc.get('target_symbol')!='BTCUSD_PERP'
                or doc.get('target_required_stream_type')!=2
                or doc.get('target_messages_observed')!=0
                or doc.get('liquidation_messages_verified_on_target_instrument') is not False
                or not isinstance(sample,list) or not 1<=len(sample)<=3
                or doc.get('observed_messages')!=len(sample)
                or any(not isinstance(x,dict) or x.get('e')!='forceOrder' or x.get('st')!=1
                       or x.get('symbol')=='BTCUSD_PERP' or x.get('side') not in ('BUY','SELL')
                       or not isinstance(x.get('sha256'),str) or len(x['sha256'])!=64
                       for x in sample)
                or any(doc.get(k) is not False for k in ('research_execution_authorized',
                       'candidate_admitted','backtest_executed','search_executed',
                       'orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed'))):
            return None
        return hashlib.sha256(raw).hexdigest()
    except (OSError,ValueError,TypeError,AttributeError):
        return None


def first_experiment_review_status():
    """Reviewability precedes replication; neither this check nor a signature grants execution."""
    try:
        for path in (PREEXPERIMENT, PREEXPERIMENT_REVIEW):
            if not path.is_file() or path.is_symlink() or path.stat().st_size > 16384:
                return None
        raw=PREEXPERIMENT.read_bytes()
        doc=json.loads(raw)
        review=json.loads(PREEXPERIMENT_REVIEW.read_bytes())
        digest=hashlib.sha256(raw).hexdigest()
        validator=runpy.run_path(str(Path(__file__).with_name('v57_prospective_causal_protocol_v1.py')))['validate']
        if validator(doc)!='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED':
            return None
        if (doc.get('kind')!='V57_PROSPECTIVE_CAUSAL_PROTOCOL_V1'
                or doc.get('hypothesis_status')!='FORMULATED_FOR_REVIEW'
                or 'BTCUSD_PERP' not in doc.get('hypothesis',{}).get('market','')
                or review.get('status')!='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'
                or review.get('submission_sha256')!=digest
                or review.get('independent_evidence_verified') is not False
                or any(doc.get(k) is not False for k in ('execution_authorized','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed'))
                or any(review.get(k) is not False for k in ('research_execution_authorized','execution_authorized','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed'))):
            return None
        return digest
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def public_liquidation_source_status():
    """Evidence of a reachable public book, NOT liquidation observations or admission."""
    try:
        if not SOURCE.is_file() or SOURCE.is_symlink() or SOURCE.stat().st_size > 16384:
            return None
        raw=SOURCE.read_bytes()
        doc=json.loads(raw)
        if (doc.get('kind')!='OMEGA_STAGE03_LIQUIDATION_PUBLIC_SOURCE_ACCESS_REVIEW_V1'
                or doc.get('status')!='PUBLIC_FUTURES_INSTRUMENT_AND_BOOK_REST_ACCESS_VERIFIED_LIQUIDATION_STREAM_UNTESTED'
                or doc.get('instrument',{}).get('symbol')!='BTCUSD_PERP'
                or doc.get('instrument',{}).get('pair')!='BTCUSD'
                or any(doc.get(k) is not False for k in ('research_execution_authorized',
                         'candidate_admitted','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed'))):
            return None
        return hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, TypeError, AttributeError):
        return None

def main():
    proposals=json.loads(P.read_text())
    data=json.loads(D.read_text())
    assert proposals['kind']=='V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1'
    assert data['kind']=='JARVIS_BTC_M1_DATA_FEASIBILITY_V1'
    assert data['supports']=='BAR_AGGREGATED_TRADE_IMBALANCE_NOT_ORDERBOOK_OR_LIQUIDATIONS'
    assert data['non_60s_intervals']==0
    public_source_sha256=public_liquidation_source_status()
    preexperiment_sha256=first_experiment_review_status()
    non_target_sample_sha256=non_target_liquidation_sample_sha256()
    rows=[]
    for p in proposals['proposals']:
        assert p['market']=='BTCUSD' and p['execution_authorized'] is False
        title=p['source_title'].lower()
        if any(term in title for term in ('liquidation','displayed depth','hidden liquidity','market making','quoting')):
            classification=('PARTIAL_PUBLIC_FUTURES_BOOK_AVAILABLE_LIQUIDATION_DATA_NOT_VERIFIED'
                            if public_source_sha256 else 'REQUIRES_UNAVAILABLE_LIQUIDATION_OR_ORDERBOOK_DATA')
        elif any(term in title for term in ('order flow','microstructure','composite alpha')):
            classification='BAR_LEVEL_PROXY_ONLY_REQUIRES_FEATURE_SPECIFICATION'
        else:
            classification='UNSPECIFIED_MECHANISM_REQUIRES_REVIEW'
        rows.append({'hypothesis_id':p['hypothesis_id'],'source_doi':p['source_doi'],'classification':classification,'status':'NOT_ADMITTED','novelty_verified':False,'execution_authorized':False})
    result={'kind':'V57_HYPOTHESIS_FEASIBILITY_TRIAGE_V1','status':'PASS_REVIEW_ONLY','reviewed':len(rows),'data_sha256':data['sha256'],'public_futures_book_source_review_sha256':public_source_sha256,'first_experiment_review_only_sha256':preexperiment_sha256,'first_experiment_status':('FORMULATED_FOR_EXTERNAL_PREEXPERIMENT_REVIEW_NOT_AUTHORIZED' if preexperiment_sha256 else 'PREEXPERIMENT_REVIEW_NOT_ESTABLISHED'),'independent_replication_required_for_first_hypothesis_review':False,'independent_replication_required_for_final_admission':True,'non_target_global_liquidation_sample_sha256':non_target_sample_sha256,'non_target_global_liquidation_status':('THREE_USDM_ST1_MESSAGES_OBSERVED_NOT_COINM_BTCUSD_PERP' if non_target_sample_sha256 else 'NO_VALID_NON_TARGET_WS_SAMPLE'),'target_instrument_forceorder_messages_verified':False,'liquidation_observations_verified':False,'independent_replication_verified':False,'items':rows,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
    tmp=O.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    tmp.replace(O)
    print('ALL PASS|HYPOTHESIS_FEASIBILITY_TRIAGE|REVIEWED='+str(len(rows))+'|AUTHORIZED=NO')

if __name__=='__main__':main()
