"""Per-market research feedback ledger; explicit missing evidence, no fake scores."""
import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def build(registry,questions,history):
    assert registry['kind']=='V57_MULTIMARKET_CANDIDATE_REGISTRY_V1'
    assert questions['kind']=='V57_MULTIMARKET_QUESTION_BUILDER_V1'
    assert history['kind']=='V57_MULTIMARKET_NOVELTY_REVIEW_V1'
    bymarket={x['market']:x for x in history['markets']}
    rows=[]
    for q in questions['questions']:
        symbol=q['market']
        records=[r for r in registry['records'] if r['market']==symbol]
        rows.append({'market':symbol,'question_status':q['status'],'source_backed_candidate_count':sum(r['hypothesis_id'] is not None for r in records),'exhausted_history_count':bymarket[symbol]['historical_exhausted_count'],'historical_rejection_known':bool(bymarket[symbol]['historical_exhausted_count']),'out_of_sample_performance':None,'independent_replication':None,'causal_novelty_verified':False,'next_step':'VALIDATE_SOURCE_AND_NOVELTY' if q.get('hypothesis') else 'OBTAIN_FEATURE_COMPATIBLE_DATA','research_authorized':False,'execution_authorized':False})
    assert len(rows)==7 and len({x['market'] for x in rows})==7
    return {'kind':'V57_MULTIMARKET_RESEARCH_FEEDBACK_V1','status':'NO_VERIFIED_NEW_EXPERIMENTAL_FEEDBACK','markets':rows,'scores_fabricated':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    def load(name):return json.loads((S/name).read_text())
    doc=build(load('multimarket_candidate_registry_v1.json'),load('multimarket_question_builder_v1.json'),load('multimarket_novelty_review_v1.json'))
    out=S/'multimarket_research_feedback_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_FEEDBACK|MARKETS=7|NEW_EXPERIMENTS=0|ORDERS=NO')

if __name__=='__main__':main()
