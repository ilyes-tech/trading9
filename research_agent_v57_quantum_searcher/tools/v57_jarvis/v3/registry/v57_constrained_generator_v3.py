import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
SRC=ROOT/"src"; V435=SRC/"v435"; V433=SRC/"v433"
for p in (V435,V433,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_native_strategy_generator_v3 as G
ENGINE="V57_JARVIS_CONSTRAINED_GENERATOR_V3"
def _bucket(domain,value):
    i=domain.index(value); return (i+0.5)/len(domain)
def generate(spec,n=1,seed=574351,start=0):
    n=int(n); start=int(start)
    if n<1 or n>32 or start<0: raise ValueError("BAD_RANGE")
    rows=G._rows(start+n,int(seed))[start:start+n].copy()
    markets=tuple(G.schema.MARKETS); tfs=tuple(G.schema.TIMEFRAMES)
    if spec.get("market") is not None:
        if spec["market"] not in markets: raise ValueError("BAD_MARKET")
        rows[:,0]=_bucket(markets,spec["market"])
    if spec.get("timeframe") is not None:
        if spec["timeframe"] not in tfs: raise ValueError("BAD_TIMEFRAME")
        rows[:,1]=_bucket(tfs,spec["timeframe"])
    if spec.get("side") is not None:
        if spec["side"] not in ("LONG","SHORT"): raise ValueError("BAD_SIDE")
        rows[:,2]=0.25 if spec["side"]=="LONG" else 0.75
    out=[G.build_strategy(rows[i],start+i) for i in range(n)]
    for s,m in out:
        if spec.get("market") and m["market"]!=spec["market"]: raise RuntimeError("MARKET_CONSTRAINT_FAILED")
        if spec.get("timeframe") and m["timeframe"]!=spec["timeframe"]: raise RuntimeError("TIMEFRAME_CONSTRAINT_FAILED")
        if spec.get("side") and m["side"]!=spec["side"]: raise RuntimeError("SIDE_CONSTRAINT_FAILED")
        if s["execution"]["orders_allowed"] is not False: raise RuntimeError("ORDERS_ENABLED")
    return out
