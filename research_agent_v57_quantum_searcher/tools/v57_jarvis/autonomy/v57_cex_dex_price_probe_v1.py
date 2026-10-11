"""Read-only bounded BTC perpetual price comparison; no execution or strategy admission."""
import argparse,datetime,hashlib,json,pathlib,urllib.parse,urllib.request

def fetch(url,payload=None):
    data=json.dumps(payload).encode() if payload else None
    req=urllib.request.Request(url,data=data,headers={'User-Agent':'TradingAI-JARVIS-Research/1.0','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=12) as r:return json.load(r)

def main():
    p=argparse.ArgumentParser();p.add_argument('--minutes',type=int,default=30);p.add_argument('--hours-ago',type=int,default=24);p.add_argument('--out',required=True);a=p.parse_args()
    if not 5<=a.minutes<=60 or not 1<=a.hours_ago<=48:raise ValueError('BOUNDS_INVALID')
    end=int((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=a.hours_ago)).replace(second=0,microsecond=0).timestamp()*1000)
    start=end-a.minutes*60000
    q=urllib.parse.urlencode({'symbol':'BTCUSDT','interval':'1m','startTime':start,'endTime':end-1,'limit':a.minutes})
    b=fetch('https://fapi.binance.com/fapi/v1/klines?'+q)
    h=fetch('https://api.hyperliquid.xyz/info',{'type':'candleSnapshot','req':{'coin':'BTC','interval':'1m','startTime':start,'endTime':end}})
    bd={int(x[0]):float(x[4]) for x in b};hd={int(x['t']):float(x['c']) for x in h}
    common=sorted(set(bd)&set(hd))
    if len(common)!=a.minutes:raise RuntimeError('INCOMPLETE_ALIGNMENT:'+str(len(common))+'/'+str(a.minutes))
    rows=[{'time_ms':t,'binance_close':bd[t],'hyperliquid_close':hd[t],'spread_bps':round(10000*(hd[t]/bd[t]-1),6)} for t in common]
    result={'kind':'V57_CEX_DEX_PRICE_PROBE_V1','status':'DESCRIPTIVE_ONLY_NOT_VALIDATED','window_start_ms':start,'window_end_ms':end,'matched_minutes':len(rows),'rows':rows,'research_execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise RuntimeError('OUTPUT_EXISTS_NO_OVERWRITE')
    content=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode();dest.write_bytes(content)
    print('ALL PASS|PRICE_ALIGNMENT|MATCHED='+str(len(rows))+'|SPREAD_BPS_MIN='+str(min(x['spread_bps'] for x in rows))+'|MAX='+str(max(x['spread_bps'] for x in rows))+'|SHA256='+hashlib.sha256(content).hexdigest()+'|ORDERS=NO')
if __name__=='__main__':
    try:main()
    except Exception as e:print('STOP|FAIL|PRICE_ALIGNMENT|'+type(e).__name__+':'+str(e));raise SystemExit(3)
