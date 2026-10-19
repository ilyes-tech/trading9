"""Market-neutral falsifiable questions; pre-registration only, never admission."""
import hashlib,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

GOLD_BACKGROUND_DOI='10.1002/1096-9934(200103)21:3<257::AID-FUT4>3.0.CO;2-W'

def eligible_gold_background(proposals):
    if not isinstance(proposals,dict) or proposals.get('kind')!='V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1':
        return False
    matches=[p for p in proposals.get('proposals',[]) if p.get('market')=='XAUUSD']
    return (len(matches)==1
        and matches[0].get('source_doi')==GOLD_BACKGROUND_DOI
        and matches[0].get('bibliographic_role')=='PUBLISHER_ABSTRACT_VOLATILITY_CONTEXT_ONLY'
        and matches[0].get('causal_dimension')=='VOLATILITY_BACKGROUND_ONLY_NOT_DIRECTIONAL_EDGE'
        and matches[0].get('portability_issue')=='COMEX_FUTURES_NOT_CURRENT_MT5_SPOT_OR_CFD_GOLD'
        and matches[0].get('execution_authorized') is False
        and all(matches[0].get(k) is False for k in ('orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed')))

def build(features,history,proposals=None):
    assert features['kind']=='V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1'
    assert history['kind']=='V57_MULTIMARKET_NOVELTY_REVIEW_V1'
    prior={x['market']:x for x in history['markets']}
    questions=[]
    for market in features['markets']:
        symbol=market['market']
        if (symbol=='XAUUSD' and market.get('price_bar_march_schema_supported') is True
                and eligible_gold_background(proposals)):
            # One scoped research QUESTION. Publisher bibliography is not a
            # transferable edge, and this is not a buy/sell strategy.
            question=('For XAUUSD M1, does the median of the last 30 completed '
                      'absolute close-to-close log returns predict the next '
                      'completed-bar absolute log return better than a lagged '
                      'expanding historical median, using a predeclared '
                      'chronological evaluation protocol?')
            fingerprint=hashlib.sha256(
                ('XAUUSD|M1|PAST_30_ABS_RETURNS|NEXT_ABS_RETURN|'+question).encode()).hexdigest()
            questions.append({
                'market':symbol,
                'status':'VOLATILITY_QUESTION_FOR_EXTERNAL_REVIEW_NOT_ADMITTED',
                'hypothesis_id':fingerprint,'hypothesis':question,
                'research_question_type':'NON_DIRECTIONAL_VOLATILITY_FORECAST',
                'feature':'median(abs(log(close[i]/close[i-1]))) for i in [t-29,t], all completed at decision t',
                'target':'abs(log(close[t+1]/close[t])) (never a feature at t)',
                'null':'lagged volatility feature does not improve forecast error over expanding historical median',
                'benchmark':'expanding median of prior completed absolute log returns at t',
                'evaluation_metric':'mean_absolute_error on a strictly future validation period, lower is better',
                'lookahead_guard':'decision at bar t close; target t+1 inaccessible at decision',
                'minimum_warmup_completed_returns':30,
                'referenced_publisher_doi':GOLD_BACKGROUND_DOI,
                'source_role':'PUBLISHER_BACKGROUND_ONLY_NOT_TRADABLE_ALPHA',
                'transfer_risk':'PAPER_COMEX_FUTURES_VS_LOCAL_MT5_XAUUSD_SPOT_CFD',
                'directional_edge_proven':False,
                'costs_verified':False,
                'independent_review_required':True,
                'history_overlap_not_ruled_out':True,
                'causality_proven':False,
                'execution_authorized':False,
            })
            continue
        if not market['bar_imbalance_feature_schema_supported']:
            questions.append({'market':symbol,'status':'BLOCKED_MISSING_FEATURE_SCHEMA','hypothesis':None,'execution_authorized':False})
            continue
        question='Does signed volume imbalance on a closed M1 bar predict the next M1 log return after chronological validation and realistic costs?'
        fingerprint=hashlib.sha256((symbol+'|M1|SIGNED_VOLUME_IMBALANCE|NEXT_BAR_LOG_RETURN|'+question).encode()).hexdigest()
        questions.append({'market':symbol,'status':'QUESTION_ONLY_NOVELTY_UNVERIFIED','hypothesis_id':fingerprint,'hypothesis':question,'feature':'(buy_volume-sell_volume)/(buy_volume+sell_volume); omit zero denominator','target':'log(close[t+1]/close[t])','historical_exhausted_count':prior[symbol]['historical_exhausted_count'],'historical_trial_count':prior[symbol].get('historical_trial_count'),'historical_sixty_second_trial_count':prior[symbol].get('historical_sixty_second_trial_count'),'historical_trial_scope':prior[symbol].get('historical_trial_scope','HISTORY_UNAVAILABLE_OR_INVALID'),'history_overlap_not_ruled_out':True,'causality_proven':False,'execution_authorized':False})
    assert len(questions)==7 and all(x['execution_authorized'] is False for x in questions)
    return {'kind':'V57_MULTIMARKET_QUESTION_BUILDER_V1','status':'PRE_REGISTRATION_ONLY','questions':questions,'specified_count':sum(x['hypothesis'] is not None for x in questions),'novelty_proven':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}

def main():
    features=json.loads((S/'multimarket_feature_eligibility_v1.json').read_text())
    history=json.loads((S/'multimarket_novelty_review_v1.json').read_text())
    proposals=json.loads((S/'evidence_hypothesis_proposals_v1.json').read_text())
    doc=build(features,history,proposals)
    out=S/'multimarket_question_builder_v1.json';temp=out.with_suffix('.tmp')
    temp.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');temp.replace(out)
    print('ALL PASS|MULTIMARKET_QUESTION_BUILDER|SPECIFIED='+str(doc['specified_count'])+'|ADMITTED=0')

if __name__=='__main__':main()
