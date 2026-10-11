"""Predeclared exploratory one-step OOS screen. Not strategy validation."""
import hashlib,json,math,pathlib,statistics
ROOT=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/work/funding_research_v1')
def main():
    source=ROOT/'BTC_CEX_DEX_24H_V1.json';data=json.loads(source.read_text());rows=data['rows']
    if len(rows)!=1440 or any(rows[i+1]['time_ms']-rows[i]['time_ms']!=60000 for i in range(1439)):raise RuntimeError('BAD_CHRONOLOGY')
    # Feature: current CEX/DEX close spread. Target: next minute Binance close-to-close return (bps).
    pairs=[(r['spread_bps'],10000*(rows[i+1]['binance_close']/r['binance_close']-1)) for i,r in enumerate(rows[:-1]) if not r['hyperliquid_inactive'] and not rows[i+1]['hyperliquid_inactive']]
    if len(pairs)<1300:raise RuntimeError('INSUFFICIENT_ACTIVITY')
    split=int(len(pairs)*.7);train,test=pairs[:split],pairs[split:];xs=[x for x,y in train];ys=[y for x,y in train]
    xm,ym=statistics.mean(xs),statistics.mean(ys);den=sum((x-xm)**2 for x in xs)
    if den<=0:raise RuntimeError('CONSTANT_FEATURE')
    slope=sum((x-xm)*(y-ym) for x,y in train)/den;intercept=ym-slope*xm
    pred=[intercept+slope*x for x,y in test];actual=[y for x,y in test]
    baseline=[ym]*len(test)
    mse=sum((p-y)**2 for p,y in zip(pred,actual))/len(test);baseline_mse=sum((p-y)**2 for p,y in zip(baseline,actual))/len(test)
    improvement=1-mse/baseline_mse if baseline_mse>0 else None
    directional=sum((p>0)==(y>0) for p,y in zip(pred,actual))/len(test)
    baseline_directional=sum((ym>0)==(y>0) for y in actual)/len(test)
    outcome={'kind':'V57_CEX_DEX_EXPLORATORY_PREDICTIVE_SCREEN_V1','status':'EXPLORATORY_NOT_ADMITTED','hypothesis':'Spread at minute t predicts Binance close-to-close return from t to t+1','train_n':len(train),'test_n':len(test),'split':'FIRST_70_PERCENT_TRAIN_LAST_30_PERCENT_TEST','feature':'hyperliquid_minus_binance_spread_bps_at_t','target':'binance_next_1m_return_bps','slope':slope,'intercept':intercept,'test_mse':mse,'baseline_test_mse':baseline_mse,'test_mse_improvement_fraction':improvement,'test_directional_accuracy':directional,'baseline_directional_accuracy':baseline_directional,'limitations':['single_24h_window','one chronological split','no costs','no independent replication','OHLCV closes not executable prices','market_microstructure_not_controlled'],'research_execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    dest=ROOT/'BTC_CEX_DEX_PREDICTIVE_SCREEN_V1.json'
    if dest.exists():raise RuntimeError('NO_OVERWRITE')
    raw=(json.dumps(outcome,sort_keys=True,indent=2)+'\n').encode();dest.write_bytes(raw)
    print('ALL PASS|EXPLORATORY_SCREEN|TRAIN='+str(len(train))+'|TEST='+str(len(test))+'|MSE_IMPROVEMENT='+str(round(improvement,6))+'|DIRECTIONAL='+str(round(directional,6))+'|BASELINE_DIRECTIONAL='+str(round(baseline_directional,6))+'|SHA256='+hashlib.sha256(raw).hexdigest()+'|ORDERS=NO')
if __name__=='__main__':
    try:main()
    except Exception as e:print('STOP|FAIL|PREDICTIVE_SCREEN|'+type(e).__name__+':'+str(e));raise SystemExit(3)
