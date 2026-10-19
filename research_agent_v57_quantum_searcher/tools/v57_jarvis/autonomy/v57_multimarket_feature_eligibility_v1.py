"""March-only feature availability: price OHLC != signed order flow != admission."""
import csv,hashlib,json
from pathlib import Path

S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
ROOT=Path('/home/trading/TradingAI-HF-Lab/historical/kraken_micro_m1/extracted')
REPO=Path('/home/trading/TradingAI-HF-Lab')
FLOW={'time','close','volume','buy_volume','sell_volume'}
PRICE={'time','open','high','low','close'}
ARCHIVE_MARKETS=frozenset(('XAUUSD','BTCUSD','ETHUSD','EURUSD','GBPUSD','USDJPY'))


def inspect(inventory, root=ROOT, repo=REPO):
    if inventory.get('kind')!='V57_MULTIMARKET_CAPABILITY_INVENTORY_V1':
        raise ValueError('INVENTORY_CONTRACT_INVALID')
    if inventory.get('later_month_files_read') is not False or inventory.get('holdout_allowed') is not False:
        raise ValueError('DEVELOPMENT_ONLY_BOUNDARY_NOT_CERTIFIED')
    rows=[]
    for market in inventory['markets']:
        symbol=market['market']
        checked=[]
        price=False
        flow=False
        for name in market['bar_files']:
            # No path strings from an untrusted file may redirect to holdout.
            if name!=symbol+'_MICRO_2026_03_M1.csv':
                raise ValueError('UNAUTHORIZED_MICROBAR_PERIOD')
            path=root/name
            if path.is_symlink() or not path.is_file():
                raise ValueError('MARCH_MICROBAR_NOT_REGULAR')
            with path.open(newline='') as f:
                columns=set(next(csv.reader(f)))
            flow=flow or FLOW.issubset(columns)
            price=price or PRICE.issubset(columns)
            checked.append({'file':name,'required_columns_present':FLOW.issubset(columns)})
        archive=market.get('verified_historical_march_dev_source')
        if archive is not None:
            if symbol not in ARCHIVE_MARKETS or archive.get('scope')!='2026-03_ONLY_DEV_M1' or archive.get('source')!='FROZEN_V56_MARCH_MANIFEST':
                raise ValueError('MARCH_DEV_ARCHIVE_SCOPE_INVALID')
            expected=(f'research_agent_v53_walkforward/data/{symbol}/{symbol}_2026_03_M1.csv'
                      if symbol in ('XAUUSD','EURUSD','GBPUSD','USDJPY')
                      else f'hf_lab/historical/kraken_micro_m1/extracted/{symbol}_MICRO_2026_03_M1.csv')
            if archive.get('file')!=expected:
                raise ValueError('ARCHIVE_FILENAME_SCOPE_INVALID')
            path=repo/expected
            if path.is_symlink() or not path.is_file():
                raise ValueError('MARCH_ARCHIVE_MISSING')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=archive.get('sha256'):
                raise ValueError('MARCH_ARCHIVE_SHA256_CHANGED')
            columns=set(next(csv.reader([raw.partition(b'\n')[0].decode('utf-8-sig')])))
            price=price or PRICE.issubset(columns)
            # Only the pinned crypto order-flow schema carries buy/sell volume.
            flow=flow or FLOW.issubset(columns)
        if price or flow:
            if market['bar_data_present'] is not True:
                raise ValueError('CAPABILITY_NOT_IN_INVENTORY')
        rows.append({'market':symbol,
                     'file_count':len(market['bar_files']),
                     'headers_checked':checked,
                     'bar_imbalance_feature_schema_supported':flow,
                     'price_bar_march_schema_supported':price,
                     'price_data_is_broker_executable':False,
                     'data_integrity_fully_verified':False,
                     'novelty_verified':False,'research_authorized':False})
    return rows


def main():
    inventory=json.loads((S/'multimarket_capability_inventory_v1.json').read_bytes())
    results=inspect(inventory)
    assert len(results)==7
    doc={'kind':'V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1',
         'status':'MARCH_SCHEMA_SCREEN_ONLY',
         'markets':results,
         'schema_supported_markets':sum(x['bar_imbalance_feature_schema_supported'] for x in results),
         'price_march_schema_supported_markets':sum(x['price_bar_march_schema_supported'] for x in results),
         'validation_or_holdout_read':False,
         'execution_authorized':False,'orders_allowed':False,
         'mt5_allowed':False,'holdout_allowed':False}
    out=S/'multimarket_feature_eligibility_v1.json'
    tmp=out.with_suffix('.tmp')
    tmp.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    tmp.replace(out)
    print('ALL PASS|MULTIMARKET_FEATURE_ELIGIBILITY|MARKETS=7|PRICE_SCHEMA='+
          str(doc['price_march_schema_supported_markets'])+'|SIGNED_FLOW_SCHEMA='+
          str(doc['schema_supported_markets'])+'|EXECUTION=DENIED')


if __name__=='__main__':
    main()
