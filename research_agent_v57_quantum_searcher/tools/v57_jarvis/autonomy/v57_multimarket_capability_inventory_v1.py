"""Seven-market March DEVELOPMENT inventory; no held-out month or execution access.

Only hash verified, frozen V56 March raw M1 development files are added
to the existing Kraken March microbar listing. Market-data presence is NOT
feature compatibility, scientific provenance admission, or broker execution.
"""
import hashlib,json
from pathlib import Path

ROOT=Path('/home/trading/TradingAI-HF-Lab/historical/kraken_micro_m1/extracted')
REPO=Path('/home/trading/TradingAI-HF-Lab')
MANIFEST=REPO/'research_agent_v56_strategy_factory/config/V56_DEV_M1_SOURCE_MANIFEST_V1.json'
MANIFEST_SHA256='8917d2a98916cd9d5f5a64f0b0ba7ab186221a34fba1dddc5bfea5b9693ed271'
STATE=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
MARKETS=('XAUUSD','BTCUSD','ETHUSD','LTCUSD','EURUSD','GBPUSD','USDJPY')
DEV_MARKETS=frozenset(('XAUUSD','BTCUSD','ETHUSD','EURUSD','GBPUSD','USDJPY'))


def verified_march_development(repo=REPO, manifest_path=MANIFEST):
    """Read trusted manifest + hashes of MARCH files only, never later months."""
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError('FROZEN_DEV_MANIFEST_NOT_AVAILABLE')
    raw=manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('FROZEN_DEV_MANIFEST_SHA256_CHANGED')
    doc=json.loads(raw)
    if doc.get('kind')!='V56_DEV_M1_SOURCE_MANIFEST_V1' or doc.get('canonical_source')!='M1_RAW':
        raise ValueError('FROZEN_DEV_MANIFEST_CONTRACT_CHANGED')
    if doc.get('research_integrity',{}).get('holdout_read') is not False:
        raise ValueError('FROZEN_MANIFEST_HOLDOUT_STATUS_INVALID')
    result={}
    for market in DEV_MARKETS:
        entries=[r for r in doc.get('entries',[]) if r.get('market')==market and r.get('month')=='2026-03']
        if len(entries)!=1:
            raise ValueError('MARCH_DEV_SOURCE_ENTRY_MISSING_OR_DUPLICATED:'+market)
        e=entries[0]
        expected=(f'research_agent_v53_walkforward/data/{market}/{market}_2026_03_M1.csv'
                  if market in ('XAUUSD','EURUSD','GBPUSD','USDJPY') else
                  f'hf_lab/historical/kraken_micro_m1/extracted/{market}_MICRO_2026_03_M1.csv')
        if e.get('path')!=expected or type(e.get('rows')) is not int or e['rows']<=0:
            raise ValueError('MARCH_DEV_FILE_CONTRACT_MISMATCH:'+market)
        path=repo/expected
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=e.get('bytes'):
            raise ValueError('MARCH_DEV_FILE_MISSING_OR_MODIFIED:'+market)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=e.get('sha256'):
            raise ValueError('MARCH_DEV_FILE_SHA256_MISMATCH:'+market)
        result[market]={'file':expected,'sha256':digest,'rows_declared':e['rows'],
                        'scope':'2026-03_ONLY_DEV_M1','source':'FROZEN_V56_MARCH_MANIFEST'}
    return result


def inventory(root=ROOT,march_sources=None):
    if march_sources is None:
        march_sources=verified_march_development()
    result=[]
    for market in MARKETS:
        # Restrict raw microbar header checking downstream to March;
        # prior glob across all months could inspect reserved month headers.
        one=root/(market+'_MICRO_2026_03_M1.csv')
        files=[one] if one.is_file() and not one.is_symlink() else []
        archive=march_sources.get(market)
        present=bool(files) or bool(archive)
        result.append({
            'market':market,
            'bar_files':[p.name for p in files],
            'bar_file_count':len(files),
            'microbar_march_present':bool(files),
            'verified_historical_march_dev_source':archive,
            'bar_data_present':present,
            'feature_schema_verified':False,
            'scientific_admission':False,'execution_authorized':False,
            'status':'MARCH_DEV_DATA_PRESENT_FEATURE_AND_COST_REVIEW_REQUIRED' if present
                     else 'NO_LOCAL_MARCH_DEV_BAR_DATA',
        })
    return result


def main():
    items=inventory()
    assert len(items)==7 and len(set(x['market'] for x in items))==7
    assert all(x['execution_authorized'] is False for x in items)
    doc={'kind':'V57_MULTIMARKET_CAPABILITY_INVENTORY_V1',
         'status':'PASS_MARCH_DEV_INVENTORY_ONLY',
         'markets':items,'market_count':7,
         'with_local_bar_data':sum(x['bar_data_present'] for x in items),
         'source_manifest_sha256':MANIFEST_SHA256,
         'later_month_files_read':False,
         'feature_verified_by_inventory':False,
         'execution_authorized':False,'orders_allowed':False,
         'mt5_allowed':False,'holdout_allowed':False}
    out=STATE/'multimarket_capability_inventory_v1.json'
    tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    tmp.replace(out)
    print('ALL PASS|MULTIMARKET_INVENTORY|MARKETS=7|MARCH_DEV_DATA_PRESENT='+
          str(doc['with_local_bar_data'])+'|EXECUTION=DENIED|HOLDOUT=NO')


if __name__=='__main__':
    main()
