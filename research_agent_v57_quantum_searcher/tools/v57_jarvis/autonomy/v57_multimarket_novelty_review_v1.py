"""Fail-closed multi-market historical overlap screening; not proof of novelty."""
import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def review(queue,agenda):
    assert queue['kind']=='V57_MULTIMARKET_RESEARCH_QUEUE_V1'
    assert agenda['kind']=='JARVIS_RESEARCH_AGENDA_V4'
    exhausted=agenda['items']
    assert all(item['status']=='EXHAUSTED' for item in exhausted)
    results=[]
    for market in queue['markets']:
        relevant=[item for item in exhausted if item['space'].startswith(market['market']+'_')]
        results.append({'market':market['market'],'historical_exhausted_count':len(relevant),'exhausted_objectives':sorted(set(x['objective'] for x in relevant)),'novelty_status':'UNVERIFIED_REQUIRES_CAUSAL_AND_HISTORY_REVIEW','research_authorized':False,'execution_authorized':False})
    assert len(results)==7
    return {'kind':'V57_MULTIMARKET_NOVELTY_REVIEW_V1','status':'SCREEN_ONLY','markets':results,'exhausted_total':len(exhausted),'novelty_proven':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    queue=json.loads((S/'multimarket_research_queue_v1.json').read_text())
    agenda=json.loads((S/'research_agenda_v4.json').read_text())
    result=review(queue,agenda)
    out=S/'multimarket_novelty_review_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_NOVELTY_REVIEW|MARKETS=7|EXHAUSTED='+str(result['exhausted_total'])+'|NOVELTY_PROVEN=NO')

if __name__=='__main__':main()
