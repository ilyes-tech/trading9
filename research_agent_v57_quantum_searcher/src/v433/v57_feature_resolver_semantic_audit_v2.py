from pathlib import Path
import sys,hashlib,json,math,datetime
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
import v57_feature_resolver_v2 as r
import v57_feature_resolver_v1 as v1
import v57_indicator_core_v1 as q

ANCHORS={
 ROOT/"src/v433/v57_feature_resolver_v2.py":"598391917542f5acda6a86408af64db4367e649336e5359f095fb781c64c2ee9",
 ROOT/"config/v433/V57_V433_MONO_CONTEXT_RUNTIME_EXPANSION_CONTRACT_V2.json":"e4cf2187dd61c94315e029b4cd44fbec97088170bd07ae7c0c8d68fd10f1a63d",
 ROOT/"src/v57_feature_resolver_v1.py":"820497b91f92f87b2a8478fccb6d269c76e450ff2daa8de18f02293e78568c41",
 ROOT/"src/v57_indicator_core_v1.py":"e29861e6837c3f8483b2e8bf56c5a1ea246d836cfe9a70dd13690436f8775384",
 ROOT/"config/V57_FEATURE_REGISTRY_V1.json":"0e8c762a44a0699de02f7b53e408276e5326f60120cab38c1a65819f980f0cee",
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def same(a,b):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
    return a.shape==b.shape and np.allclose(a,b,rtol=0.0,atol=0.0,equal_nan=True)
def close(a,b):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
    return a.shape==b.shape and np.allclose(a,b,rtol=2e-6,atol=1e-8,equal_nan=True)
def fail(fn,label):
    try: fn()
    except Exception: return
    raise AssertionError("EXPECTED_FAIL:"+label)
def base(z):
    return tuple(np.asarray(z[k],dtype=(np.int64 if k=="time" else float)) for k in ("time","open","high","low","close","volume"))
def cases():
    return [
      ({"family":"momentum","feature":"STOCHASTIC","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.stochastic(h,l,c,t,s,14)),
      ({"family":"momentum","feature":"ROC","parameters":{"window":10}},lambda t,o,h,l,c,v,s:q.roc(c,t,s,10)),
      ({"family":"momentum","feature":"CCI","parameters":{"window":20}},lambda t,o,h,l,c,v,s:q.cci(h,l,c,t,s,20)),
      ({"family":"momentum","feature":"WILLIAMS_R","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.williams_r(h,l,c,t,s,14)),
      ({"family":"momentum","feature":"ULTIMATE_OSCILLATOR","parameters":{"parameter_set":[7,14,28]}},lambda t,o,h,l,c,v,s:q.ultimate_oscillator(h,l,c,t,s,7,14,28)),
      ({"family":"momentum","feature":"FISHER_TRANSFORM","parameters":{"window":10}},lambda t,o,h,l,c,v,s:q.fisher_transform(h,l,t,s,10)),
      ({"family":"trend","feature":"SMA","parameters":{"window":20}},lambda t,o,h,l,c,v,s:q.sma(c,t,s,20)),
      ({"family":"trend","feature":"EMA","parameters":{"window":20}},lambda t,o,h,l,c,v,s:q.ema(c,t,s,20)),
      ({"family":"trend","feature":"ADX","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.adx(h,l,c,t,s,14)[0]),
      ({"family":"trend","feature":"PLUS_DI","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.adx(h,l,c,t,s,14)[1]),
      ({"family":"trend","feature":"MINUS_DI","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.adx(h,l,c,t,s,14)[2]),
      ({"family":"volatility","feature":"ATR","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.atr(h,l,c,t,s,14)),
      ({"family":"volatility","feature":"NATR","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.natr(h,l,c,t,s,14)),
      ({"family":"volume","feature":"CMF","parameters":{"window":20}},lambda t,o,h,l,c,v,s:q.cmf(h,l,c,v,t,s,20)),
      ({"family":"volume","feature":"MFI","parameters":{"window":14}},lambda t,o,h,l,c,v,s:q.mfi(h,l,c,v,t,s,14)),
      ({"family":"volume","feature":"VWAP_DISTANCE","parameters":{}},lambda t,o,h,l,c,v,s:10000.0*(q.safe_div(c,q.vwap(h,l,c,v,t,s))-1.0)),
      ({"family":"time","feature":"weekday_sin","parameters":{}},lambda t,o,h,l,c,v,s:np.sin(2*math.pi*np.mod(np.floor_divide(t,86400)+3,7)/7.0)),
      ({"family":"time","feature":"weekday_cos","parameters":{}},lambda t,o,h,l,c,v,s:np.cos(2*math.pi*np.mod(np.floor_divide(t,86400)+3,7)/7.0)),
    ]

for p,h in ANCHORS.items(): assert sha(p)==h,(p,sha(p))
assert len(r.NEW_FEATURES)==18

tfsec={"M5":300,"M15":900,"M30":1800,"H1":3600}
files=sorted((ROOT/"work/feature_cache_v1").glob("*/*_V57_FEATURE_CACHE_V1.npz"))
assert len(files)==24,len(files)
resolve_checks=0
cache_parity=0
for p in files:
    z=np.load(p,allow_pickle=False)
    tf=p.name.split("_")[1]; sec=tfsec[tf]; market=p.parent.name
    vals=base(z)
    cache={k:z[k] for k in z.files}
    for cond,oracle in cases():
        got=r.resolve_feature(cache,cond,sec,market)
        exp=oracle(*vals,sec)
        assert same(got,exp),(market,tf,cond["feature"])
        resolve_checks+=1
    for cond,key in [
      ({"family":"trend","feature":"ADX","parameters":{"window":14}},"adx_14"),
      ({"family":"trend","feature":"PLUS_DI","parameters":{"window":14}},"plus_di_14"),
      ({"family":"trend","feature":"MINUS_DI","parameters":{"window":14}},"minus_di_14"),
      ({"family":"volatility","feature":"ATR","parameters":{"window":14}},"atr_14"),
      ({"family":"volatility","feature":"NATR","parameters":{"window":14}},"natr_14"),
      ({"family":"volume","feature":"CMF","parameters":{"window":20}},"cmf_20"),
      ({"family":"volume","feature":"MFI","parameters":{"window":14}},"mfi_14"),
    ]:
        assert key in z.files,(p,key)
        assert close(r.resolve_feature(cache,cond,sec,market),z[key]),(market,tf,key)
        cache_parity+=1

# Independent weekday calendar oracle.
days=np.arange(0,28,dtype=np.int64)*86400
wc={k:np.ones(len(days),dtype=float) for k in ("open","high","low","close","volume")}; wc["time"]=days
wd=np.array([datetime.datetime.fromtimestamp(int(x),tz=datetime.timezone.utc).weekday() for x in days],dtype=float)
assert same(r.resolve_feature(wc,{"family":"time","feature":"weekday_sin","parameters":{}},300),np.sin(2*math.pi*wd/7))
assert same(r.resolve_feature(wc,{"family":"time","feature":"weekday_cos","parameters":{}},300),np.cos(2*math.pi*wd/7))

# Causality + segment reset on synthetic data.
sec=300; n=260; t=np.arange(n,dtype=np.int64)*sec; t[150:]+=4*sec
x=np.arange(n,dtype=float); c=100+.03*x+2*np.sin(x/9); o=c+.2*np.sin(x/5); h=np.maximum(o,c)+.8; l=np.minimum(o,c)-.7; v=1000+2*x+30*np.sin(x/7)
sc={"time":t,"open":o,"high":h,"low":l,"close":c,"volume":v}
cut=220; prefix_checks=0; gap_checks=0
for cond,_ in cases():
    full=r.resolve_feature(sc,cond,sec)
    pre={k:np.asarray(a)[:cut] for k,a in sc.items()}
    assert same(np.asarray(full)[:cut],r.resolve_feature(pre,cond,sec)),("PREFIX",cond["feature"])
    prefix_checks+=1
    if cond["family"]!="time":
        suf={k:np.asarray(a)[150:] for k,a in sc.items()}
        assert same(np.asarray(full)[150:],r.resolve_feature(suf,cond,sec)),("GAP_RESET",cond["feature"])
        gap_checks+=1

# Exact V1 delegation across all 26 V1-supported feature branches.
vc=dict(sc)
for k in ("hour_sin","hour_cos","obv","vwap","trades","vol_imbalance","count_imbalance","market_volume_share","market_trade_share","avg_trade_size","avg_buy_size","avg_sell_size"):
    vc[k]=np.linspace(1,2,n)
v1_cases=[
 {"family":"time","feature":"hour_sin","parameters":{}},{"family":"time","feature":"hour_cos","parameters":{}},
 {"family":"volume","feature":"volume","parameters":{}},{"family":"volume","feature":"OBV","parameters":{}},{"family":"volume","feature":"VWAP","parameters":{}},
 *[{"family":"crypto_microstructure","feature":f,"parameters":{}} for f in ("trades","vol_imbalance","count_imbalance","market_volume_share","market_trade_share","avg_trade_size","avg_buy_size","avg_sell_size")],
 {"family":"momentum","feature":"RSI","parameters":{"window":14}},
 {"family":"momentum","feature":"STOCH_RSI","parameters":{"rsi_window":14,"stoch_window":14}},
 {"family":"trend","feature":"MACD","parameters":{"fast":12,"slow":26,"signal":9}},
 {"family":"trend","feature":"PPO","parameters":{"fast":12,"slow":26,"signal":9}},
 {"family":"trend","feature":"SUPERTREND","parameters":{"window":10,"multiplier":3.0}},
 {"family":"volatility","feature":"TRUE_RANGE","parameters":{}},
 {"family":"volatility","feature":"BOLLINGER_BANDS","parameters":{"window":20,"multiplier":2.0}},
 {"family":"volatility","feature":"BOLLINGER_WIDTH","parameters":{"window":20,"multiplier":2.0}},
 {"family":"volatility","feature":"BOLLINGER_PERCENT_B","parameters":{"window":20,"multiplier":2.0}},
 {"family":"volatility","feature":"DONCHIAN_CHANNEL","parameters":{"window":20}},
 {"family":"price_action","feature":"body","parameters":{}},{"family":"price_action","feature":"range","parameters":{}},{"family":"price_action","feature":"close_location","parameters":{}},
]
assert len(v1_cases)==26
for cond in v1_cases: assert same(r.resolve_feature(vc,cond,sec),v1.resolve_feature(vc,cond,sec)),cond["feature"]

# Parameter and deferred-feature fail-closed.
bad=[
 {"family":"volatility","feature":"NATR","parameters":{}},
 {"family":"volatility","feature":"NATR","parameters":{"window":14.0}},
 {"family":"volatility","feature":"NATR","parameters":{"window":6}},
 {"family":"volume","feature":"VWAP_DISTANCE","parameters":{"window":5}},
 {"family":"time","feature":"weekday_sin","parameters":{"x":1}},
 {"family":"momentum","feature":"ULTIMATE_OSCILLATOR","parameters":{"parameter_set":[7,14,27]}},
]
for i,cnd in enumerate(bad): fail(lambda cnd=cnd:r.resolve_feature(sc,cnd,sec),f"BAD_PARAM_{i}")
fail(lambda:r.resolve_feature(sc,{"family":"volatility","feature":"ATR","parameters":{"window":14}},0),"BAD_SEC")
deferred=[
 ("market_structure","breakout_high"),("market_structure","breakout_low"),
 ("price_action","inside_bar"),("price_action","outside_bar"),("price_action","momentum_bar"),
 ("time","session_asia"),("time","session_london"),("time","session_newyork"),("time","session_overlap"),
 ("volatility","range_expansion"),("volatility","range_contraction"),
]
for fam,feat in deferred: fail(lambda fam=fam,feat=feat:r.resolve_feature(sc,{"family":fam,"feature":feat,"parameters":{}},sec),feat)

# Actual market-specific microstructure availability; no fabricated zeros.
micro=("trades","vol_imbalance","count_imbalance","market_volume_share","market_trade_share","avg_trade_size","avg_buy_size","avg_sell_size")
micro_checks=0
for p in files:
    z=np.load(p,allow_pickle=False); cache={k:z[k] for k in z.files}; tf=p.name.split("_")[1]; s=tfsec[tf]; m=p.parent.name
    has=all(k in z.files for k in micro)
    assert has==(m in ("BTCUSD","ETHUSD")),(m,tf,has)
    for f in micro:
        cond={"family":"crypto_microstructure","feature":f,"parameters":{}}
        if has: assert same(r.resolve_feature(cache,cond,s,m),z[f])
        else: fail(lambda cond=cond,cache=cache,s=s,m=m:r.resolve_feature(cache,cond,s,m),m+":"+tf+":"+f)
        micro_checks+=1

print(f"V57_V433_FEATURE_RESOLVER_SEMANTIC_AUDIT_V2|RESOLVE_CHECKS={resolve_checks}|CACHE_PARITY={cache_parity}|V1_DELEGATION=26|PREFIX_CAUSAL={prefix_checks}|GAP_RESET={gap_checks}|MICRO_CHECKS={micro_checks}|DEFERRED_FAIL_CLOSED={len(deferred)}")
print("V57_V433_FEATURE_RESOLVER_SEMANTIC_AUDIT_V2=PASS|18_FEATURES=PASS|24_CONTEXTS=PASS|WEEKDAY_CALENDAR_ORACLE=PASS|PARAM_FAIL_CLOSED=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")
