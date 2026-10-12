"""One deterministic cross-market research decision, without market preference or trading permission."""
import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
MARKETS=('XAUUSD','BTCUSD','ETHUSD','LTCUSD','EURUSD','GBPUSD','USDJPY')
def decide(inventory,queue,features,history,registry,feedback):
    inputs=(inventory,queue,features,history,feedback)
    keys=('markets','markets','markets','markets','markets')
    assert all(len(doc[key])==7 for doc,key in zip(inputs,keys))
    assert all(tuple(x['market'] for x in doc[key])==MARKETS for doc,key in zip(inputs,keys))
    assert registry['markets_covered']==7
    assert all(doc.get('execution_authorized') is False for doc in (*inputs,registry))
    by_feature={x['market']:x for x in features['markets']}
    by_queue={x['market']:x for x in queue['markets']}
    by_history={x['market']:x for x in history['markets']}
    by_feedback={x['market']:x for x in feedback['markets']}
    rows=[]
    for market in MARKETS:
        q=by_queue[market];f=by_feature[market];h=by_history[market];fb=by_feedback[market]
        if not q['bar_data_present']:next_action='ACQUIRE_AND_VERIFY_MARKET_DATA'
        elif not f['bar_imbalance_feature_schema_supported']:next_action='VERIFY_REQUIRED_FEATURE_SCHEMA'
        elif h.get('historical_trial_scope', 'HISTORY_UNAVAILABLE_OR_INVALID') == 'HISTORY_UNAVAILABLE_OR_INVALID':next_action='VERIFY_HISTORICAL_SEARCH_COVERAGE'
        elif isinstance(h.get('historical_trial_count'), int) and not isinstance(h.get('historical_trial_count'), bool) and h['historical_trial_count'] > 0:next_action='REVIEW_PRIOR_FLOW_TRIALS_AND_MECHANISM_DIFFERENCE'
        elif not fb['source_backed_candidate_count']:next_action='FIND_INDEPENDENT_SOURCE_EVIDENCE'
        else:next_action='REVIEW_CAUSAL_NOVELTY_AND_MEASUREMENT'
        rows.append({'market':market,'next_action':next_action,'historical_trial_count':h.get('historical_trial_count'),'historical_sixty_second_trial_count':h.get('historical_sixty_second_trial_count'),'historical_trial_scope':h.get('historical_trial_scope','HISTORY_UNAVAILABLE_OR_INVALID'),'exhausted_history_count':h['historical_exhausted_count'],'source_backed_candidate_count':fb['source_backed_candidate_count'],'admitted_hypotheses':0,'research_authorized':False,'execution_authorized':False})
    return {'kind':'V57_MULTIMARKET_RESEARCH_DECISION_V1','status':'BLOCKED_PENDING_SCIENTIFIC_EVIDENCE','policy':'PER_MARKET_EVIDENCE_GAPS_NO_ARBITRARY_PRIORITY','markets':rows,'market_count':7,'admitted_hypotheses':0,'search_executed':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
def main():
    def load(name):return json.loads((S/name).read_text())
    doc=decide(load('multimarket_capability_inventory_v1.json'),load('multimarket_research_queue_v1.json'),load('multimarket_feature_eligibility_v1.json'),load('multimarket_novelty_review_v1.json'),load('multimarket_candidate_registry_v1.json'),load('multimarket_research_feedback_v1.json'))
    out=S/'multimarket_research_decision_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_DECISION|MARKETS=7|ADMITTED=0|ORDERS=NO')
if __name__=='__main__':main()
