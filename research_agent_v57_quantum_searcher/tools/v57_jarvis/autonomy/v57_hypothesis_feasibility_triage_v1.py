import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
P=S/'evidence_hypothesis_proposals_v1.json'
D=Path('/root/jarvis-migration/btc-m1-data-feasibility-20261011.json')
O=S/'hypothesis_feasibility_triage_v1.json'

def main():
    proposals=json.loads(P.read_text())
    data=json.loads(D.read_text())
    assert proposals['kind']=='V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1'
    assert data['kind']=='JARVIS_BTC_M1_DATA_FEASIBILITY_V1'
    assert data['supports']=='BAR_AGGREGATED_TRADE_IMBALANCE_NOT_ORDERBOOK_OR_LIQUIDATIONS'
    assert data['non_60s_intervals']==0
    rows=[]
    for p in proposals['proposals']:
        assert p['market']=='BTCUSD' and p['execution_authorized'] is False
        title=p['source_title'].lower()
        if any(term in title for term in ('liquidation','displayed depth','hidden liquidity','market making','quoting')):
            classification='REQUIRES_UNAVAILABLE_LIQUIDATION_OR_ORDERBOOK_DATA'
        elif any(term in title for term in ('order flow','microstructure','composite alpha')):
            classification='BAR_LEVEL_PROXY_ONLY_REQUIRES_FEATURE_SPECIFICATION'
        else:
            classification='UNSPECIFIED_MECHANISM_REQUIRES_REVIEW'
        rows.append({'hypothesis_id':p['hypothesis_id'],'source_doi':p['source_doi'],'classification':classification,'status':'NOT_ADMITTED','novelty_verified':False,'execution_authorized':False})
    result={'kind':'V57_HYPOTHESIS_FEASIBILITY_TRIAGE_V1','status':'PASS_REVIEW_ONLY','reviewed':len(rows),'data_sha256':data['sha256'],'items':rows,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
    tmp=O.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    tmp.replace(O)
    print('ALL PASS|HYPOTHESIS_FEASIBILITY_TRIAGE|REVIEWED='+str(len(rows))+'|AUTHORIZED=NO')

if __name__=='__main__':main()
