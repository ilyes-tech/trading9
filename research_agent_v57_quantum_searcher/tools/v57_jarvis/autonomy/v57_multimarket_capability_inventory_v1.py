"""Generic seven-market data capability inventory, research-only."""
import json
from pathlib import Path
ROOT=Path('/home/trading/TradingAI-HF-Lab/historical/kraken_micro_m1/extracted')
STATE=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
MARKETS=('XAUUSD','BTCUSD','ETHUSD','LTCUSD','EURUSD','GBPUSD','USDJPY')

def inventory(root=ROOT):
    result=[]
    for market in MARKETS:
        files=sorted(root.glob(market+'_MICRO_????_??_M1.csv'))
        result.append({'market':market,'bar_files':[p.name for p in files],'bar_file_count':len(files),'bar_data_present':bool(files),'scientific_admission':False,'execution_authorized':False,'status':'DATA_PRESENT_REQUIRES_VALIDATION' if files else 'MISSING_LOCAL_BAR_DATA'})
    return result

def main():
    items=inventory()
    assert len(items)==7 and len(set(x['market'] for x in items))==7
    assert all(x['execution_authorized'] is False for x in items)
    doc={'kind':'V57_MULTIMARKET_CAPABILITY_INVENTORY_V1','status':'PASS_INVENTORY_ONLY','markets':items,'market_count':7,'with_local_bar_data':sum(x['bar_data_present'] for x in items),'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    out=STATE/'multimarket_capability_inventory_v1.json'
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_INVENTORY|MARKETS=7|DATA_PRESENT='+str(doc['with_local_bar_data'])+'|EXECUTION=DENIED')

if __name__=='__main__':main()
