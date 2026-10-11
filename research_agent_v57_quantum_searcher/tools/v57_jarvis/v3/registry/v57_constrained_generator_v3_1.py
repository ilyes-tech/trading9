import v57_constrained_generator_v3 as B
G=B.G
ENGINE="V57_JARVIS_CONSTRAINED_GENERATOR_V3_1"
def _force_family(row,market,family,offset):
    pool=tuple(x for x in G.feature_pool(market) if x[0]==family)
    if not pool: raise ValueError("EMPTY_FAMILY:"+family)
    full=G.feature_pool(market)
    targets=[i for i,x in enumerate(full) if x in pool]
    i=targets[int(float(row[offset%len(row)])*len(targets))%len(targets)]
    row[offset%len(row)]=(i+0.5)/len(full)
def generate(spec,n=1,seed=574351,start=0):
    n=int(n); start=int(start)
    if n<1 or n>32 or start<0: raise ValueError("BAD_RANGE")
    rows=G._rows(start+n,int(seed))[start:start+n].copy()
    markets=tuple(G.schema.MARKETS); tfs=tuple(G.schema.TIMEFRAMES)
    market=spec.get("market")
    if market:
        if market not in markets: raise ValueError("BAD_MARKET")
        rows[:,0]=B._bucket(markets,market)
    if spec.get("timeframe"):
        if spec["timeframe"] not in tfs: raise ValueError("BAD_TIMEFRAME")
        rows[:,1]=B._bucket(tfs,spec["timeframe"])
    if spec.get("side"):
        if spec["side"] not in ("LONG","SHORT"): raise ValueError("BAD_SIDE")
        rows[:,2]=0.25 if spec["side"]=="LONG" else 0.75
    fam=tuple(spec.get("families") or ())
    if fam and not market: raise ValueError("FAMILY_REQUIRES_MARKET")
    for row in rows:
        for j in range(G.MAX_CONDITIONS):
            if fam: _force_family(row,market,fam[j%len(fam)],4+j*6)
    out=[G.build_strategy(rows[i],start+i) for i in range(n)]
    for s,m in out:
        if market and m["market"]!=market: raise RuntimeError("MARKET_CONSTRAINT_FAILED")
        if spec.get("timeframe") and m["timeframe"]!=spec["timeframe"]: raise RuntimeError("TIMEFRAME_CONSTRAINT_FAILED")
        if spec.get("side") and m["side"]!=spec["side"]: raise RuntimeError("SIDE_CONSTRAINT_FAILED")
        if fam and any(c["family"] not in fam for c in m["conditions"]): raise RuntimeError("FAMILY_CONSTRAINT_FAILED")
        if s["execution"]["orders_allowed"] is not False: raise RuntimeError("ORDERS_ENABLED")
    return out
