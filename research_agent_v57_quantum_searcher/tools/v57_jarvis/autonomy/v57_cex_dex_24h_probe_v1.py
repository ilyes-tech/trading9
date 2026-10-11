"""Single bounded 24h CEX/DEX research sample, read-only and fail-closed."""
import datetime,hashlib,json,pathlib,statistics,urllib.parse,urllib.request

def get(url,body=None):
    r=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,headers={'Content-Type':'application/json','User-Agent':'TradingAI-JARVIS-Research/1.0'})
    with urllib.request.urlopen(r,timeout=25) as f:return json.load(f)

def main():
    end=int((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=24)).replace(second=0,microsecond=0).timestamp()*1000)
    start=end-1440*60000
    binance=[]
    for offset in (0,720):
        args=urllib.parse.urlencode({'symbol':'BTCUSDT','interval':'1m','startTime':start+offset*60000,'endTime':start+(offset+720)*60000-1,'limit':720})
        binance.extend(get('https://fapi.binance.com/fapi/v1/klines?'+args))
    hyper=get('https://api.hyperliquid.xyz/info',{'type':'candleSnapshot','req':{'coin':'BTC','interval':'1m','startTime':start,'endTime':end}})
    b={int(x[0]):x for x in binance};h={int(x['t']):x for x in hyper if start<=int(x['t'])<end}
    expected=[start+i*60000 for i in range(1440)]
    if len(binance)!=1440 or len(b)!=1440 or len(h)!=1440 or set(expected)!=set(b) or set(expected)!=set(h):raise RuntimeError('INCOMPLETE_OR_DUPLICATE_MINUTES')
    rows=[]
    for t in expected:
        x,y=b[t],h[t];bc,hc=float(x[4]),float(y['c']);bv,hv=float(x[5]),float(y['v']);hn=int(y['n'])
        if min(bc,hc)<=0 or min(bv,hv)<0 or hn<0:raise RuntimeError('BAD_PRICE_OR_NEGATIVE_ACTIVITY')
        rows.append({'time_ms':t,'binance_close':bc,'hyperliquid_close':hc,'binance_volume':bv,'hyperliquid_volume':hv,'hyperliquid_trades':hn,'hyperliquid_inactive':hv==0 or hn==0,'spread_bps':round(10000*(hc/bc-1),6)})
    s=[r['spread_bps'] for r in rows]
    result={'kind':'V57_CEX_DEX_24H_PROBE_V1','status':'DESCRIPTIVE_ONLY_NOT_VALIDATED','start_ms':start,'end_ms_exclusive':end,'count':len(rows),'hyperliquid_inactive_minutes':sum(x['hyperliquid_inactive'] for x in rows),'mean_spread_bps':statistics.mean(s),'min_spread_bps':min(s),'max_spread_bps':max(s),'rows':rows,'research_execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
    path=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/work/funding_research_v1/BTC_CEX_DEX_24H_V1.json');path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise RuntimeError('NO_OVERWRITE')
    raw=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode();path.write_bytes(raw)
    print('ALL PASS|24H_ALIGNED=1440|MEAN_SPREAD_BPS='+str(round(statistics.mean(s),5))+'|RANGE_BPS='+str((min(s),max(s)))+'|SHA256='+hashlib.sha256(raw).hexdigest()+'|ORDERS=NO')
if __name__=='__main__':
    try:main()
    except Exception as e:print('STOP|FAIL|24H_PROBE|'+type(e).__name__+':'+str(e));raise SystemExit(3)
