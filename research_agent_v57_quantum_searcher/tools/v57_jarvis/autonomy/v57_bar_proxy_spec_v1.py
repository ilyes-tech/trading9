"""Conservative pre-registration of a measurable bar-level research question."""
import hashlib,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
D=Path('/root/jarvis-migration/btc-m1-data-feasibility-20261011.json')
T=S/'hypothesis_feasibility_triage_v1.json'
O=S/'bar_proxy_spec_v1.json'

def main():
    data=json.loads(D.read_text()); triage=json.loads(T.read_text())
    assert data['kind']=='JARVIS_BTC_M1_DATA_FEASIBILITY_V1' and data['non_60s_intervals']==0
    assert data['rows']==43200 and data['supports']=='BAR_AGGREGATED_TRADE_IMBALANCE_NOT_ORDERBOOK_OR_LIQUIDATIONS'
    assert all(x in data['fields'] for x in ('time','close','volume','buy_volume','sell_volume'))
    candidates=[x for x in triage['items'] if x['classification']=='BAR_LEVEL_PROXY_ONLY_REQUIRES_FEATURE_SPECIFICATION']
    assert len(candidates)==1 and candidates[0]['status']=='NOT_ADMITTED'
    spec={'market':'BTCUSD','frequency':'M1','research_question':'Does lagged bar-level signed-volume imbalance associate with next-bar log return out of sample?','feature':'(buy_volume-sell_volume)/(buy_volume+sell_volume) at closed bar t; undefined when denominator is zero','target':'log(close[t+1]/close[t])','controls':['no contemporaneous target leakage','chronological train/validation split','cost and execution realism required before trading claims','independent untouched holdout required for final assessment'],'limitations':['bar aggregates are not order-book imbalance','no liquidation labels','no causal claim from correlation','June 2026 already inspected; not pristine holdout'],'candidate_id':candidates[0]['hypothesis_id'],'data_sha256':data['sha256'],'status':'SPECIFICATION_ONLY_NOT_ADMITTED','novelty_verified':False,'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
    spec['spec_sha256']=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
    tmp=O.with_suffix('.tmp');tmp.write_text(json.dumps(spec,indent=2,sort_keys=True)+'\n');tmp.replace(O)
    print('ALL PASS|BAR_PROXY_SPEC|CANDIDATES=1|EXECUTION=DENIED')

if __name__=='__main__':main()
