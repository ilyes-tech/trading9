"""Per-market research feedback ledger; explicit missing evidence, no fake scores."""
import hashlib,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def build(registry,questions,history,resolution=None):
    assert registry['kind']=='V57_MULTIMARKET_CANDIDATE_REGISTRY_V1'
    assert questions['kind']=='V57_MULTIMARKET_QUESTION_BUILDER_V1'
    assert history['kind']=='V57_MULTIMARKET_NOVELTY_REVIEW_V1'
    bymarket={x['market']:x for x in history['markets']}
    rows=[]
    for q in questions['questions']:
        symbol=q['market']
        records=[r for r in registry['records'] if r['market']==symbol]
        h = bymarket[symbol]
        trial_count = h.get('historical_trial_count')
        next_step = 'VALIDATE_SOURCE_AND_NOVELTY' if q.get('hypothesis') else 'OBTAIN_FEATURE_COMPATIBLE_DATA'
        if q.get('hypothesis'):
            if h.get('historical_trial_scope', 'HISTORY_UNAVAILABLE_OR_INVALID') == 'HISTORY_UNAVAILABLE_OR_INVALID':
                next_step = 'VERIFY_HISTORICAL_SEARCH_COVERAGE'
            elif isinstance(trial_count, int) and not isinstance(trial_count, bool) and trial_count > 0:
                next_step = 'REVIEW_PRIOR_FLOW_TRIALS_AND_MECHANISM_DIFFERENCE'
        closed = (isinstance(resolution,dict)
                  and resolution.get('kind') == 'OMEGA_STAGE03_HYPOTHESIS_REVIEW_RESOLUTION_V1'
                  and resolution.get('status') == 'REJECT_FOR_NEW_FAMILY_ADMISSION'
                  and resolution.get('causal_family_gate') == 'DENY_EXISTING_OR_EXHAUSTED_FAMILY'
                  and resolution.get('native_family') == 'volume'
                  and resolution.get('existing_hypothesis_id') == q.get('hypothesis_id')
                  and type(trial_count) is int and trial_count > 0
                  and resolution.get('historical_trials_in_registry') == trial_count
                  and all(resolution.get(k) is False for k in ('research_execution_authorized','orders_allowed','mt5_allowed','holdout_allowed')))
        if closed:
            next_step = 'STOP_REJECTED_EXISTING_FLOW_HYPOTHESIS'
        rows.append({'market':symbol,'question_status':q['status'],'source_backed_candidate_count':sum(r['hypothesis_id'] is not None for r in records),'exhausted_history_count':bymarket[symbol]['historical_exhausted_count'],'historical_rejection_known':bool(bymarket[symbol]['historical_exhausted_count']),'out_of_sample_performance':None,'independent_replication':None,'causal_novelty_verified':False,'historical_trial_count':trial_count,'historical_sixty_second_trial_count':h.get('historical_sixty_second_trial_count'),'historical_trial_scope':h.get('historical_trial_scope','HISTORY_UNAVAILABLE_OR_INVALID'),'scientific_review_status':'REJECTED_EXISTING_FAMILY' if closed else 'UNRESOLVED','reviewed_hypothesis_id':q.get('hypothesis_id') if closed else None,'next_step':next_step,'research_authorized':False,'execution_authorized':False})
    assert len(rows)==7 and len({x['market'] for x in rows})==7
    return {'kind':'V57_MULTIMARKET_RESEARCH_FEEDBACK_V1','status':'NO_VERIFIED_NEW_EXPERIMENTAL_FEEDBACK','markets':rows,'scores_fabricated':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    def load(name):return json.loads((S/name).read_text())
    question_path=S/'multimarket_question_builder_v1.json'
    questions=json.loads(question_path.read_text())
    resolution_path=S/'stage03_hypothesis_review_resolution_v1.json'
    resolution=None
    if resolution_path.is_file() and not resolution_path.is_symlink() and resolution_path.stat().st_size <= 16384:
        try:
            record=json.loads(resolution_path.read_text())
            if record.get('question_registry_sha256') == hashlib.sha256(question_path.read_bytes()).hexdigest():
                resolution=record
        except (ValueError,TypeError,UnicodeError):
            pass
    doc=build(load('multimarket_candidate_registry_v1.json'),questions,load('multimarket_novelty_review_v1.json'),resolution)
    out=S/'multimarket_research_feedback_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_FEEDBACK|MARKETS=7|NEW_EXPERIMENTS=0|ORDERS=NO')

if __name__=='__main__':main()
