"""Fail-closed multi-market historical overlap screening; not proof of novelty."""
import csv,hashlib,io,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')


def prior_search_summary(path):
    """Describe one historical TRAIN campaign; never establish novelty/admission."""
    unavailable = {'status': 'UNAVAILABLE_OR_INVALID', 'by_market': {}, 'source_sha256': None}
    try:
        raw = path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        if not rows:
            return unavailable
        seen, markets = set(), {}
        for row in rows:
            symbol = {'BTC/USD': 'BTCUSD', 'ETH/USD': 'ETHUSD'}[row['symbol']]
            horizon = int(row['horizon_seconds'])
            if row['stage'] != 'TRAIN' or horizon not in (5, 15, 30, 60, 90):
                return unavailable
            if row['family'] not in ('FLOW_MOMENTUM', 'PRICE_FLOW_CONSENSUS', 'FLOW_REVERSAL', 'BURST_IMPULSE', 'EXTREME_CONSENSUS') or row['profile'] not in ('P01', 'P02', 'P03', 'P04', 'P05', 'P06'):
                return unavailable
            key = (symbol, row['family'], row['profile'], horizon)
            if key in seen:
                return unavailable
            seen.add(key)
            item = markets.setdefault(symbol, {'configuration_count': 0, 'sixty_second_horizon_count': 0})
            item['configuration_count'] += 1
            item['sixty_second_horizon_count'] += int(horizon == 60)
        return {'status': 'HISTORICAL_TRAIN_CAMPAIGN_ONLY', 'by_market': markets, 'source_sha256': hashlib.sha256(raw).hexdigest()}
    except (OSError, UnicodeError, ValueError, KeyError, csv.Error):
        return unavailable

def review(queue,agenda,prior_search=None):
    assert queue['kind']=='V57_MULTIMARKET_RESEARCH_QUEUE_V1'
    assert agenda['kind']=='JARVIS_RESEARCH_AGENDA_V4'
    prior_search = prior_search or {'status': 'UNAVAILABLE_OR_INVALID', 'by_market': {}, 'source_sha256': None}
    exhausted=agenda['items']
    assert all(item['status']=='EXHAUSTED' for item in exhausted)
    results=[]
    for market in queue['markets']:
        relevant=[item for item in exhausted if item['space'].startswith(market['market']+'_')]
        results.append({'market':market['market'],'historical_exhausted_count':len(relevant),'exhausted_objectives':sorted(set(x['objective'] for x in relevant)),'novelty_status':'UNVERIFIED_REQUIRES_CAUSAL_AND_HISTORY_REVIEW','research_authorized':False,'execution_authorized':False})
    for item in results:
        trial = prior_search['by_market'].get(item['market'])
        item['historical_trial_count'] = trial['configuration_count'] if trial else None
        item['historical_sixty_second_trial_count'] = trial['sixty_second_horizon_count'] if trial else None
        item['historical_trial_scope'] = ('PRIOR_FLOW_CAMPAIGN_FOUND_EXACT_DUPLICATE_UNPROVEN' if trial else ('NO_MATCH_IN_THIS_CAMPAIGN_NOT_PROOF_OF_NOVELTY' if prior_search['status'] == 'HISTORICAL_TRAIN_CAMPAIGN_ONLY' else 'HISTORY_UNAVAILABLE_OR_INVALID'))
    assert len(results)==7
    return {'kind':'V57_MULTIMARKET_NOVELTY_REVIEW_V1','status':'SCREEN_ONLY','prior_search':prior_search,'markets':results,'exhausted_total':len(exhausted),'novelty_proven':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

def main():
    queue=json.loads((S/'multimarket_research_queue_v1.json').read_text())
    agenda=json.loads((S/'research_agenda_v4.json').read_text())
    historical = Path('/home/trading/TradingAI-HF-Lab/hf_lab/results/phase4f3a_train_search.csv')
    result=review(queue,agenda,prior_search_summary(historical))
    out=S/'multimarket_novelty_review_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_NOVELTY_REVIEW|MARKETS=7|EXHAUSTED='+str(result['exhausted_total'])+'|NOVELTY_PROVEN=NO')

if __name__=='__main__':main()
