import v57_constrained_generator_v3_2 as B
G=B.G
ENGINE="V57_JARVIS_CONSTRAINED_GENERATOR_V4"
BLOCKED_FOR_PRICE_ACTION={"RISING_N","FALLING_N","CROSS_RECENT_N","CROSS_AND_HOLD_N","CROSS_AND_RETEST_N"}
def generate(spec,n=1,seed=574351,start=0):
    fam=tuple(spec.get("families") or ())
    if "price_action" not in fam:
        return B.generate(spec,n=n,seed=seed,start=start)
    if fam!=("price_action",):
        raise ValueError("PRICE_ACTION_MUST_BE_ISOLATED")
    n=int(n); start=int(start)
    if n<1 or n>32 or start<0: raise ValueError("BAD_RANGE")
    out=[]; cursor=start; attempts=0
    while len(out)<n and attempts<4096:
        rows=G._rows(cursor+1,int(seed)); row=rows[cursor].copy(); logic=G.READY[cursor%len(G.READY)]
        cursor+=1; attempts+=1
        if logic in BLOCKED_FOR_PRICE_ACTION: continue
        market=spec.get("market")
        if not market: raise ValueError("FAMILY_REQUIRES_MARKET")
        markets=tuple(G.schema.MARKETS); tfs=tuple(G.schema.TIMEFRAMES)
        if market not in markets: raise ValueError("BAD_MARKET")
        row[0]=B.B._bucket(markets,market)
        if spec.get("timeframe"):
            if spec["timeframe"] not in tfs: raise ValueError("BAD_TIMEFRAME")
            row[1]=B.B._bucket(tfs,spec["timeframe"])
        if spec.get("side"):
            if spec["side"] not in ("LONG","SHORT"): raise ValueError("BAD_SIDE")
            row[2]=0.25 if spec["side"]=="LONG" else 0.75
        for j in range(G.MAX_CONDITIONS): B._force_family(row,market,"price_action",4+j*6)
        s,m=G.build_strategy(row,cursor-1)
        if m["logic"] in BLOCKED_FOR_PRICE_ACTION: raise RuntimeError("BLOCKED_LOGIC_ESCAPED")
        if any(x["family"]!="price_action" for x in m["conditions"]): raise RuntimeError("PRICE_ACTION_CONSTRAINT_FAILED")
        if s["execution"]["orders_allowed"] is not False: raise RuntimeError("ORDERS_ENABLED")
        out.append((s,m))
    if len(out)!=n: raise RuntimeError("PRICE_ACTION_GENERATION_EXHAUSTED")
    return out
