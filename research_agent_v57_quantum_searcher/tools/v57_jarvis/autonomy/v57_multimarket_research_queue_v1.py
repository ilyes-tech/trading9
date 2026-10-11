"""Evidence-constrained multi-market research queue, never execution admission."""
import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def build(inventory,proposals,feasibility):
    assert inventory['kind']=='V57_MULTIMARKET_CAPABILITY_INVENTORY_V1'
    assert proposals['kind']=='V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1'
    assert feasibility['kind']=='V57_HYPOTHESIS_FEASIBILITY_TRIAGE_V1'
    classifications={x['hypothesis_id']:x['classification'] for x in feasibility['items']}
    queue=[]
    for market in inventory['markets']:
        ideas=[p for p in proposals['proposals'] if p['market']==market['market']]
        feasible=[p for p in ideas if classifications.get(p['hypothesis_id'])=='BAR_LEVEL_PROXY_ONLY_REQUIRES_FEATURE_SPECIFICATION']
        status='NEEDS_LOCAL_DATA' if not market['bar_data_present'] else ('EVIDENCE_GAP' if not ideas else ('FEATURE_REVIEW_REQUIRED' if feasible else 'UNSUPPORTED_MECHANISMS'))
        queue.append({'market':market['market'],'bar_data_present':market['bar_data_present'],'literature_ideas':len(ideas),'feature_review_candidates':len(feasible),'status':status,'scientific_admission':False,'execution_authorized':False})
    assert len(queue)==7 and all(not x['execution_authorized'] for x in queue)
    return {'kind':'V57_MULTIMARKET_RESEARCH_QUEUE_V1','status':'REVIEW_ONLY','markets':queue,'priority_policy':'EVIDENCE_AND_DATA_GAPS_NOT_ARBITRARY_MARKET_RANKING','execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    inventory=json.loads((S/'multimarket_capability_inventory_v1.json').read_text())
    proposals=json.loads((S/'evidence_hypothesis_proposals_v1.json').read_text())
    feasibility=json.loads((S/'hypothesis_feasibility_triage_v1.json').read_text())
    doc=build(inventory,proposals,feasibility)
    out=S/'multimarket_research_queue_v1.json';temp=out.with_suffix('.tmp')
    temp.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');temp.replace(out)
    print('ALL PASS|MULTIMARKET_RESEARCH_QUEUE|MARKETS=7|EXECUTION=DENIED')

if __name__=='__main__':main()
