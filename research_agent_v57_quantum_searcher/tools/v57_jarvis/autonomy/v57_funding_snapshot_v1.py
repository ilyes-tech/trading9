"""Bounded, read-only funding history snapshot; no trading or admission actions."""
import argparse,datetime,hashlib,json,pathlib,urllib.parse,urllib.request

def get(url,payload=None):
    req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload else None,headers={'User-Agent':'TradingAI-JARVIS-Research/1.0','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=12) as r:return json.load(r)

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',default='2025-08-01');p.add_argument('--days',type=int,default=1);p.add_argument('--out',required=True);a=p.parse_args()
    if not 1<=a.days<=2:raise ValueError('DAYS_MUST_BE_1_OR_2')
    start=int(datetime.datetime.strptime(a.start,'%Y-%m-%d').replace(tzinfo=datetime.timezone.utc).timestamp()*1000);end=start+a.days*86400000
    rows=[]
    b=get('https://fapi.binance.com/fapi/v1/fundingRate?'+urllib.parse.urlencode({'symbol':'BTCUSDT','startTime':start,'endTime':end-1,'limit':1000}))
    for x in b:rows.append({'venue':'binance','time_ms':int(x['fundingTime']),'rate':float(x['fundingRate'])})
    y=get('https://api.bybit.com/v5/market/funding/history?'+urllib.parse.urlencode({'category':'linear','symbol':'BTCUSDT','startTime':start,'endTime':end-1,'limit':200}))
    if y.get('retCode')!=0:raise RuntimeError('BYBIT_RESPONSE_ERROR')
    for x in y['result']['list']:rows.append({'venue':'bybit','time_ms':int(x['fundingRateTimestamp']),'rate':float(x['fundingRate'])})
    h=get('https://api.hyperliquid.xyz/info',{'type':'fundingHistory','coin':'BTC','startTime':start,'endTime':end})
    if len(h)>=500:raise RuntimeError('HYPERLIQUID_PAGINATION_REQUIRED_FAIL_CLOSED')
    for x in h:rows.append({'venue':'hyperliquid','time_ms':int(x['time']),'rate':float(x['fundingRate'])})
    if any(not start<=x['time_ms']<end for x in rows):raise RuntimeError('OUT_OF_RANGE')
    rows.sort(key=lambda x:(x['venue'],x['time_ms']))
    for venue in ('binance','bybit','hyperliquid'):
        t=[x['time_ms'] for x in rows if x['venue']==venue]
        if not t or len(t)!=len(set(t)):raise RuntimeError('MISSING_OR_DUPLICATE:'+venue)
    result={'kind':'V57_FUNDING_SNAPSHOT_V1','status':'RAW_READ_ONLY_NOT_VALIDATED','start':a.start,'days':a.days,'counts':{v:sum(x['venue']==v for x in rows) for v in ('binance','bybit','hyperliquid')},'rows':rows,'research_execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise RuntimeError('OUTPUT_EXISTS_NO_OVERWRITE')
    content=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode();dest.write_bytes(content)
    print('ALL PASS|FUNDING_SNAPSHOT|READ_ONLY|COUNTS='+json.dumps(result['counts'],sort_keys=True)+'|SHA256='+hashlib.sha256(content).hexdigest()+'|ORDERS=NO')
if __name__=='__main__':
    try:main()
    except Exception as e:print('STOP|FAIL|FUNDING_SNAPSHOT|'+type(e).__name__+':'+str(e));raise SystemExit(3)
