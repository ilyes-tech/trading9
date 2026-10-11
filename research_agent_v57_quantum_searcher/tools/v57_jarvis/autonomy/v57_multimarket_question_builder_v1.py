"""Market-neutral falsifiable questions; pre-registration only, never admission."""
import hashlib,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')

def build(features,history):
    assert features['kind']=='V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1'
    assert history['kind']=='V57_MULTIMARKET_NOVELTY_REVIEW_V1'
    prior={x['market']:x for x in history['markets']}
    questions=[]
    for market in features['markets']:
        symbol=market['market']
        if not market['bar_imbalance_feature_schema_supported']:
            questions.append({'market':symbol,'status':'BLOCKED_MISSING_FEATURE_SCHEMA','hypothesis':None,'execution_authorized':False})
            continue
        question='Does signed volume imbalance on a closed M1 bar predict the next M1 log return after chronological validation and realistic costs?'
        fingerprint=hashlib.sha256((symbol+'|M1|SIGNED_VOLUME_IMBALANCE|NEXT_BAR_LOG_RETURN|'+question).encode()).hexdigest()
        questions.append({'market':symbol,'status':'QUESTION_ONLY_NOVELTY_UNVERIFIED','hypothesis_id':fingerprint,'hypothesis':question,'feature':'(buy_volume-sell_volume)/(buy_volume+sell_volume); omit zero denominator','target':'log(close[t+1]/close[t])','historical_exhausted_count':prior[symbol]['historical_exhausted_count'],'history_overlap_not_ruled_out':True,'causality_proven':False,'execution_authorized':False})
    assert len(questions)==7 and all(x['execution_authorized'] is False for x in questions)
    return {'kind':'V57_MULTIMARKET_QUESTION_BUILDER_V1','status':'PRE_REGISTRATION_ONLY','questions':questions,'specified_count':sum(x['hypothesis'] is not None for x in questions),'novelty_proven':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}

def main():
    features=json.loads((S/'multimarket_feature_eligibility_v1.json').read_text())
    history=json.loads((S/'multimarket_novelty_review_v1.json').read_text())
    doc=build(features,history)
    out=S/'multimarket_question_builder_v1.json';temp=out.with_suffix('.tmp')
    temp.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');temp.replace(out)
    print('ALL PASS|MULTIMARKET_QUESTION_BUILDER|SPECIFIED='+str(doc['specified_count'])+'|ADMITTED=0')

if __name__=='__main__':main()
