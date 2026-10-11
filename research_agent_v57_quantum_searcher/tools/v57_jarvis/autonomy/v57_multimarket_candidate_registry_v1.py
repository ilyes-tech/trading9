"""Market-neutral candidate registry; no synthetic novelty or execution admission."""
import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def build(inventory,proposals,eligibility,agenda):
    assert inventory['kind']=='V57_MULTIMARKET_CAPABILITY_INVENTORY_V1'
    assert eligibility['kind']=='V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1'
    assert agenda['kind']=='JARVIS_RESEARCH_AGENDA_V4'
    assert agenda['active'] is None
    exhausted={x['id'] for x in agenda['items'] if x['status']=='EXHAUSTED'}
    supported={x['market']:x['bar_imbalance_feature_schema_supported'] for x in eligibility['markets']}
    records=[]; seen=set()
    for market in inventory['markets']:
        symbol=market['market']
        source_proposals=[p for p in proposals['proposals'] if p['market']==symbol]
        for p in source_proposals:
            hid=p['hypothesis_id']
            if hid in seen:continue
            seen.add(hid)
            records.append({'market':symbol,'hypothesis_id':hid,'source_doi':p['source_doi'],'data_schema_supported':supported.get(symbol,False),'duplicate_exhausted_id':hid in exhausted,'status':'HISTORICALLY_EXHAUSTED' if hid in exhausted else 'NOVELTY_AND_CAUSAL_EVIDENCE_UNVERIFIED','execution_authorized':False})
        if not source_proposals:
            records.append({'market':symbol,'hypothesis_id':None,'source_doi':None,'data_schema_supported':supported.get(symbol,False),'duplicate_exhausted_id':False,'status':'NO_SOURCE_BACKED_HYPOTHESIS','execution_authorized':False})
    assert {x['market'] for x in records}=={x['market'] for x in inventory['markets']}
    assert all(not x['execution_authorized'] for x in records)
    return {'kind':'V57_MULTIMARKET_CANDIDATE_REGISTRY_V1','status':'EVIDENCE_GAP_REVIEW_ONLY','records':records,'markets_covered':7,'source_backed_candidates':sum(x['hypothesis_id'] is not None for x in records),'novelty_proven':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    def load(name):return json.loads((S/name).read_text())
    doc=build(load('multimarket_capability_inventory_v1.json'),load('evidence_hypothesis_proposals_v1.json'),load('multimarket_feature_eligibility_v1.json'),load('research_agenda_v4.json'))
    out=S/'multimarket_candidate_registry_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_CANDIDATE_REGISTRY|MARKETS=7|SOURCED='+str(doc['source_backed_candidates'])+'|NOVELTY=UNVERIFIED|EXECUTION=DENIED')

if __name__=='__main__':main()
