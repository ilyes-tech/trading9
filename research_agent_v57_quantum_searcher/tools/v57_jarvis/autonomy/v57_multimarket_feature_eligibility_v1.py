"""Read-only market-neutral feature feasibility, not scientific admission."""
import csv,json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
ROOT=Path('/home/trading/TradingAI-HF-Lab/historical/kraken_micro_m1/extracted')
FIELDS={'time','close','volume','buy_volume','sell_volume'}

def main():
    inventory=json.loads((S/'multimarket_capability_inventory_v1.json').read_text())
    assert inventory['kind']=='V57_MULTIMARKET_CAPABILITY_INVENTORY_V1'
    results=[]
    for market in inventory['markets']:
        files=market['bar_files']; checked=[]
        for name in files:
            path=ROOT/name
            with path.open(newline='') as f:
                reader=csv.reader(f); header=next(reader)
            checked.append({'file':name,'required_columns_present':FIELDS.issubset(set(header))})
        supported=bool(checked) and all(x['required_columns_present'] for x in checked)
        results.append({'market':market['market'],'file_count':len(files),'headers_checked':checked,'bar_imbalance_feature_schema_supported':supported,'data_integrity_fully_verified':False,'novelty_verified':False,'research_authorized':False})
    assert len(results)==7
    doc={'kind':'V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1','status':'SCHEMA_SCREEN_ONLY','markets':results,'schema_supported_markets':sum(x['bar_imbalance_feature_schema_supported'] for x in results),'execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    out=S/'multimarket_feature_eligibility_v1.json';tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');tmp.replace(out)
    print('ALL PASS|MULTIMARKET_FEATURE_ELIGIBILITY|MARKETS=7|SCHEMA_SUPPORTED='+str(doc['schema_supported_markets'])+'|EXECUTION=DENIED')

if __name__=='__main__':main()
