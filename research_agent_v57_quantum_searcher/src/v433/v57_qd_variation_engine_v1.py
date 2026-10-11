from pathlib import Path
import copy,hashlib,json,random,sys
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_native_strategy_generator_v1 as gen
import v57_screening_generator_v1 as legacy_gen
import v57_strategy_dsl_v3 as dsl3
import v57_logic_registry_compiler_v2 as compiler
ENGINE="V57_V433_QD_VARIATION_ENGINE_V1"
POLICY=ROOT/"config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
EXPECTED={"policy":"d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f","generator":"2d0698578dcb1e09eeb935cf96db672b8b41d55a96edd6704b03d2d93adb0afd","generator_freeze":"205f3f4f09477a4117daef21effceec61f7f6125cc00cce3df98c51e76a82dc9","runtime_v3_freeze":"89c9561e7e38848ef60d5febbf5873d7580926c6328074ea6a990c91bd5dc968","replay_freeze":"b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626","dsl3":"8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b","compiler":"a5f1dcd7d557dac35940bbdcf0faffcdcc6ed460f97cf0e28aa183c0fbf37077","resolver":"598391917542f5acda6a86408af64db4367e649336e5359f095fb781c64c2ee9"}
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _policy(): return json.loads(POLICY.read_text())
def _ensure():
    paths={"policy":POLICY,"generator":V433/"v57_native_strategy_generator_v1.py","generator_freeze":ROOT/"config/v433/V57_V433_NATIVE_STRATEGY_GENERATOR_V1_FREEZE_V1.json","runtime_v3_freeze":ROOT/"config/v433/V57_V433_SEARCH_RUNTIME_V3_FREEZE_V1.json","replay_freeze":ROOT/"config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json","dsl3":V433/"v57_strategy_dsl_v3.py","compiler":V433/"v57_logic_registry_compiler_v2.py","resolver":V433/"v57_feature_resolver_v2.py"}
    got={k:H(v) for k,v in paths.items()}
    if got!=EXPECTED: raise RuntimeError("QD_VARIATION_ANCHOR_MISMATCH:"+str(got))
    p=_policy()
    if p.get("status")!="FROZEN_BEFORE_QD_ENGINEERING_IMPLEMENTATION" or p.get("next_stage")!="V433_QD_VARIATION_ENGINE_V1": raise RuntimeError("QD_POLICY_STATE_MISMATCH")
    vc=p["variation_contract"]
    if vc.get("status")!="NOT_IMPLEMENTED_IN_POLICY": raise RuntimeError("QD_VARIATION_POLICY_STATE_CHANGED")
    gen._ensure()
    return True
P=_policy()
OPERATORS=tuple(P["variation_contract"]["required_operator_families"])
MUTATION_STEPS=tuple(int(x) for x in P["variation_contract"]["historical_mutation_steps"])
U=legacy_gen.U
TRANSFORMS=tuple(U["transforms"]); LOOKBACKS=tuple(U["lookbacks"]); QUANTILES=tuple(U["threshold_quantiles"])
RISK_DOMAINS={"atr_window":tuple(U["risk_models"]["atr_windows"]),"atr_multiplier":tuple(U["risk_models"]["atr_multipliers"]),"rr":tuple(U["risk_models"]["rr"])}
BOLLINGER={("volatility","BOLLINGER_BANDS"),("volatility","BOLLINGER_WIDTH"),("volatility","BOLLINGER_PERCENT_B")}
def _neighbor(seq,val,rng):
    x=list(seq)
    if not x: raise ValueError("EMPTY_DOMAIN")
    if val not in x: return copy.deepcopy(rng.choice(x))
    i=x.index(val); z=[x[j] for j in (i-1,i+1) if 0<=j<len(x)]
    return copy.deepcopy(rng.choice(z or [val]))
def _legacy_params_valid(c):
    fam,feat=c["family"],c["feature"]; p=c["parameters"]; r=gen._registry()
    if (fam,feat)==("momentum","RSI"): return set(p)=={"window"} and p["window"] in r["momentum"]["RSI"]["windows"]
    if (fam,feat)==("momentum","STOCH_RSI"): return set(p)=={"rsi_window","stoch_window"} and p["rsi_window"] in r["momentum"]["STOCH_RSI"]["rsi_windows"] and p["stoch_window"] in r["momentum"]["STOCH_RSI"]["stoch_windows"]
    if fam=="trend" and feat in ("MACD","PPO"): return set(p)=={"fast","slow","signal"} and [p["fast"],p["slow"],p["signal"]] in [list(x) for x in r["trend"][feat]["parameter_sets"]]
    if (fam,feat)==("trend","SUPERTREND"): return set(p)=={"window","multiplier"} and p["window"] in r["trend"]["SUPERTREND"]["windows"] and p["multiplier"] in r["trend"]["SUPERTREND"]["multipliers"]
    if (fam,feat) in BOLLINGER: return set(p)=={"window","multiplier"} and p["window"] in r["volatility"]["BOLLINGER"]["windows"] and p["multiplier"] in r["volatility"]["BOLLINGER"]["multipliers"]
    if (fam,feat)==("volatility","DONCHIAN_CHANNEL"): return set(p)=={"window"} and p["window"] in r["volatility"]["DONCHIAN"]["windows"]
    return p=={}
def _condition_valid(market,c):
    pair=(c.get("family"),c.get("feature"))
    if pair not in set(gen.feature_pool(market)): return False
    if c.get("transform") not in TRANSFORMS or c.get("lookback") not in LOOKBACKS or c.get("threshold_quantile") not in QUANTILES: return False
    if not isinstance(c.get("parameters"),dict): return False
    if pair in set(gen.NEW_FEATURES):
        try: gen._validate_new_condition(c)
        except Exception: return False
        return True
    return _legacy_params_valid(c)
def validate_recipe(r):
    if r.get("market") not in gen.schema.MARKETS or r.get("timeframe") not in gen.schema.TIMEFRAMES or r.get("side") not in ("LONG","SHORT"): raise ValueError("BAD_RECIPE_MARKET")
    logic=r.get("logic"); conditions=r.get("conditions")
    if logic not in gen.READY or not isinstance(conditions,list): raise ValueError("BAD_RECIPE_LOGIC")
    n=len(conditions)
    if not 1<=n<=4 or n not in gen._allowed_counts(logic): raise ValueError("BAD_RECIPE_ARITY")
    if len({dsl3.canonical_json(c) for c in conditions})!=n: raise ValueError("DUPLICATE_RECIPE_CONDITION")
    if not all(_condition_valid(r["market"],c) for c in conditions): raise ValueError("BAD_RECIPE_CONDITION")
    compiler.compile_logic(logic,[compiler.condition_node(c) for c in conditions],**r.get("logic_params",{}))
    risk=r.get("risk",{})
    if risk.get("stop")!="ATR" or risk.get("take_profit")!="RR" or risk.get("break_even") is not False or risk.get("trailing_stop") is not False: raise ValueError("BAD_RECIPE_RISK_SEMANTICS")
    if risk.get("atr_window") not in RISK_DOMAINS["atr_window"] or risk.get("atr_multiplier") not in RISK_DOMAINS["atr_multiplier"] or risk.get("rr") not in RISK_DOMAINS["rr"]: raise ValueError("BAD_RECIPE_RISK_DOMAIN")
    if risk.get("time_stop_bars") not in tuple(U["risk_models"]["time_stop_bars"][r["timeframe"]]): raise ValueError("BAD_RECIPE_TIME_STOP")
    if risk.get("structure_lookback") not in tuple(U["risk_models"]["structure_lookbacks"]): raise ValueError("BAD_RECIPE_STRUCTURE_LOOKBACK")
    return True
def recipe_from_pair(strategy,meta):
    n=int(meta["children"]); r={"market":meta["market"],"timeframe":meta["timeframe"],"side":meta["side"],"logic":meta["logic"],"logic_params":copy.deepcopy(meta.get("logic_params",{})),"conditions":copy.deepcopy(meta["conditions"][:n]),"risk":copy.deepcopy(strategy["risk"])}; validate_recipe(r); return r
def strategy_from_recipe(r):
    validate_recipe(r); n=len(r["conditions"]); node=compiler.compile_logic(r["logic"],[compiler.condition_node(c) for c in r["conditions"]],**copy.deepcopy(r["logic_params"]))
    s={"schema_version":3,"kind":"V57_STRATEGY_DSL_V3","market":{"symbol":r["market"],"timeframe":r["timeframe"],"side":r["side"]},"signal":node,"risk":copy.deepcopy(r["risk"]),"execution":{"mode":"RESEARCH_ONLY","orders_allowed":False},"portfolio":{"enabled":False},"research_integrity":{"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"real_orders_allowed":False,"demo_orders_allowed":False},"legacy":{"source_dsl":"NATIVE_V433_QD","generator":ENGINE,"search_logic":r["logic"],"search_logic_params":copy.deepcopy(r["logic_params"]),"search_child_count":n}}
    s=dsl3.finalize_strategy(s); m={"market":r["market"],"timeframe":r["timeframe"],"side":r["side"],"logic":r["logic"],"logic_params":copy.deepcopy(r["logic_params"]),"children":n,"conditions":copy.deepcopy(r["conditions"])}; return s,m
def _logic_params_for(name,n,rng):
    if name in gen.N_PARAM: return {"n":int(rng.choice(tuple(gen.N_DOMAIN)))}
    if name in gen.K_POSITIVE: return {"k":int(rng.randrange(1,n+1))}
    if name in gen.K_ZERO_OK: return {"k":int(rng.randrange(0,n+1))}
    return {}
def _repair_logic_params(r):
    n=len(r["conditions"]); name=r["logic"]; p=copy.deepcopy(r.get("logic_params",{}))
    if name in gen.N_PARAM: p={"n":p.get("n",gen.N_DOMAIN[0]) if p.get("n") in gen.N_DOMAIN else gen.N_DOMAIN[0]}
    elif name in gen.K_POSITIVE: p={"k":max(1,min(n,int(p.get("k",1))))}
    elif name in gen.K_ZERO_OK: p={"k":max(0,min(n,int(p.get("k",0))))}
    else: p={}
    r["logic_params"]=p
def _fresh_condition(market,rng,exclude=None,family_not=None):
    pool=[x for x in gen.feature_pool(market) if x!=exclude and (family_not is None or x[0]!=family_not)]
    if not pool: raise ValueError("NO_FRESH_CONDITION")
    fam,feat=rng.choice(pool); row=[rng.random() for _ in range(48)]; return gen.condition_for_feature(fam,feat,row,4)
def _mutate_parameters(c,rng):
    c=copy.deepcopy(c); fam,feat=c["family"],c["feature"]; p=c["parameters"]; r=gen._registry()
    if (fam,feat)==("momentum","ULTIMATE_OSCILLATOR"):
        p["parameter_set"]=_neighbor(r["momentum"]["ULTIMATE_OSCILLATOR"]["parameter_sets"],list(p["parameter_set"]),rng); return c
    if (fam,feat)==("momentum","STOCH_RSI"):
        k=rng.choice(("rsi_window","stoch_window")); dom=r["momentum"]["STOCH_RSI"]["rsi_windows" if k=="rsi_window" else "stoch_windows"]; p[k]=_neighbor(dom,p[k],rng); return c
    if fam=="trend" and feat in ("MACD","PPO"):
        z=_neighbor(r["trend"][feat]["parameter_sets"],[p["fast"],p["slow"],p["signal"]],rng); p.update({"fast":z[0],"slow":z[1],"signal":z[2]}); return c
    if (fam,feat)==("trend","SUPERTREND"):
        k=rng.choice(("window","multiplier")); p[k]=_neighbor(r["trend"]["SUPERTREND"]["windows" if k=="window" else "multipliers"],p[k],rng); return c
    if (fam,feat) in BOLLINGER:
        k=rng.choice(("window","multiplier")); p[k]=_neighbor(r["volatility"]["BOLLINGER"]["windows" if k=="window" else "multipliers"],p[k],rng); return c
    if (fam,feat)==("volatility","DONCHIAN_CHANNEL"):
        p["window"]=_neighbor(r["volatility"]["DONCHIAN"]["windows"],p["window"],rng); return c
    if "window" in p:
        pair=(fam,feat); rfam,rfeat=gen.REGISTRY_ALIAS.get(pair,pair); p["window"]=_neighbor(r[rfam][rfeat]["windows"],p["window"],rng); return c
    raise ValueError("FEATURE_PARAMETERS_NOT_MUTABLE:"+fam+":"+feat)
def mutate_recipe(recipe,operator,seed,donors=()):
    _ensure(); r=copy.deepcopy(recipe); validate_recipe(r); rng=random.Random(int(seed)); n=len(r["conditions"])
    if operator not in OPERATORS: raise ValueError("UNKNOWN_VARIATION_OPERATOR:"+str(operator))
    if operator=="threshold_neighbor":
        j=rng.randrange(n); r["conditions"][j]["threshold_quantile"]=_neighbor(QUANTILES,r["conditions"][j]["threshold_quantile"],rng)
    elif operator=="lookback_neighbor":
        j=rng.randrange(n); r["conditions"][j]["lookback"]=_neighbor(LOOKBACKS,r["conditions"][j]["lookback"],rng)
    elif operator=="transform_neighbor":
        j=rng.randrange(n); r["conditions"][j]["transform"]=_neighbor(TRANSFORMS,r["conditions"][j]["transform"],rng)
    elif operator=="feature_parameter_neighbor":
        ids=[i for i,c in enumerate(r["conditions"]) if c.get("parameters")]
        if not ids: raise ValueError("MUTATION_NOT_APPLICABLE:feature_parameter_neighbor")
        j=rng.choice(ids); r["conditions"][j]=_mutate_parameters(r["conditions"][j],rng)
    elif operator=="logic_neighbor":
        name=r["logic"]; changed=False
        if name in gen.N_PARAM and rng.random()<0.5:
            q=r["logic_params"]["n"]; r["logic_params"]["n"]=_neighbor(gen.N_DOMAIN,q,rng); changed=r["logic_params"]["n"]!=q
        elif name in gen.K_POSITIVE and n>1 and rng.random()<0.5:
            q=r["logic_params"]["k"]; r["logic_params"]["k"]=_neighbor(tuple(range(1,n+1)),q,rng); changed=r["logic_params"]["k"]!=q
        elif name in gen.K_ZERO_OK and n>1 and rng.random()<0.5:
            q=r["logic_params"]["k"]; r["logic_params"]["k"]=_neighbor(tuple(range(0,n+1)),q,rng); changed=r["logic_params"]["k"]!=q
        if not changed:
            choices=[x for x in gen.READY if x!=name and n in gen._allowed_counts(x)]
            if not choices: raise ValueError("MUTATION_NOT_APPLICABLE:logic_neighbor")
            r["logic"]=rng.choice(choices); r["logic_params"]=_logic_params_for(r["logic"],n,rng)
    elif operator=="condition_replace":
        j=rng.randrange(n); old=r["conditions"][j]
        for _ in range(32):
            c=_fresh_condition(r["market"],rng,exclude=(old["family"],old["feature"]))
            if c!=old: r["conditions"][j]=c; break
        else: raise ValueError("MUTATION_NOT_APPLICABLE:condition_replace")
    elif operator=="condition_drop":
        if n<=1 or (n-1) not in gen._allowed_counts(r["logic"]): raise ValueError("MUTATION_NOT_APPLICABLE:condition_drop")
        del r["conditions"][rng.randrange(n)]; _repair_logic_params(r)
    elif operator=="condition_add":
        if n>=4 or (n+1) not in gen._allowed_counts(r["logic"]): raise ValueError("MUTATION_NOT_APPLICABLE:condition_add")
        r["conditions"].append(_fresh_condition(r["market"],rng)); _repair_logic_params(r)
    elif operator=="risk_neighbor":
        k=rng.choice(("atr_window","atr_multiplier","rr","time_stop_bars")); dom=tuple(U["risk_models"]["time_stop_bars"][r["timeframe"]]) if k=="time_stop_bars" else RISK_DOMAINS[k]; r["risk"][k]=_neighbor(dom,r["risk"][k],rng)
    elif operator=="cross_family_recombination":
        fams={c["family"] for c in r["conditions"]}; candidates=[]
        for d in donors:
            if d.get("market")!=r["market"]: continue
            for c in d.get("conditions",[]):
                if c["family"] not in fams and _condition_valid(r["market"],c): candidates.append(copy.deepcopy(c))
        if not candidates: raise ValueError("MUTATION_NOT_APPLICABLE:cross_family_recombination")
        r["conditions"][rng.randrange(n)]=rng.choice(candidates)
    if r==recipe: raise ValueError("MUTATION_NO_CHANGE:"+operator)
    validate_recipe(r); return r
def mutate_sequence(recipe,seed,donors=(),steps=None):
    rng=random.Random(int(seed)); q=copy.deepcopy(recipe); used=[]
    lo=min(MUTATION_STEPS); hi=max(MUTATION_STEPS); count=int(steps) if steps is not None else rng.randint(lo,hi)
    if count<lo or count>hi: raise ValueError("BAD_MUTATION_STEP_COUNT")
    for _ in range(count):
        order=list(OPERATORS); rng.shuffle(order); done=False
        for op in order:
            try:
                q=mutate_recipe(q,op,rng.randrange(1,2**63),donors); used.append(op); done=True; break
            except ValueError:
                continue
        if not done: raise ValueError("NO_APPLICABLE_VARIATION_OPERATOR")
    validate_recipe(q); return q,used
def generate_offspring(parent_strategy,parent_meta,count,seed,donor_pairs=()):
    parent=recipe_from_pair(parent_strategy,parent_meta); donors=[recipe_from_pair(s,m) for s,m in donor_pairs]; out=[]; seen={parent_strategy["strategy_id"]}; master=random.Random(int(seed)); attempts=0
    while len(out)<int(count) and attempts<max(300,int(count)*100):
        sub=master.randrange(1,2**63); attempts+=1
        try: r,ops=mutate_sequence(parent,sub,donors); s,m=strategy_from_recipe(r)
        except ValueError: continue
        if s["strategy_id"] in seen: continue
        seen.add(s["strategy_id"]); out.append((s,m,{"operators":ops,"steps":len(ops),"seed":sub}))
    if len(out)!=int(count): raise RuntimeError("INSUFFICIENT_UNIQUE_QD_OFFSPRING:%d/%d"%(len(out),int(count)))
    return out
def self_check():
    _ensure()
    if len(OPERATORS)!=10 or set(OPERATORS)!=set(P["variation_contract"]["required_operator_families"]): raise AssertionError("OPERATOR_CONTRACT_MISMATCH")
    if MUTATION_STEPS!=(1,3): raise AssertionError("MUTATION_STEP_CONTRACT_CHANGED")
    pairs=gen.generate(256,943402,0); recipes=[recipe_from_pair(s,m) for s,m in pairs]; checked={}
    for oi,op in enumerate(OPERATORS):
        found=None
        for pi,(s,m) in enumerate(pairs):
            try:
                q=mutate_recipe(recipes[pi],op,943500+oi*1000+pi,recipes); z,mm=strategy_from_recipe(q)
                if q==recipes[pi]: continue
                validate_recipe(q); dsl3.validate_strategy(z); found=(pi,q,z,mm); break
            except ValueError: continue
        if found is None: raise AssertionError("OPERATOR_NOT_COVERED:"+op)
        pi,q,z,mm=found; q2=mutate_recipe(recipes[pi],op,943500+oi*1000+pi,recipes); z2,mm2=strategy_from_recipe(q2)
        if q2!=q or z2!=z or mm2!=mm: raise AssertionError("NONDETERMINISTIC_OPERATOR:"+op)
        checked[op]=z["strategy_id"]
    if len(checked)!=10: raise AssertionError("OPERATOR_COVERAGE_COUNT")
    for r in recipes:
        if r["market"] not in legacy_gen.CRYPTO and any(c["family"]=="crypto_microstructure" for c in r["conditions"]): raise AssertionError("MICROSTRUCTURE_SCOPE_VIOLATION")
    s0,m0=pairs[0]; kids=generate_offspring(s0,m0,20,944001,pairs[1:120])
    if len(kids)!=20 or len({x[0]["strategy_id"] for x in kids})!=20: raise AssertionError("OFFSPRING_DEDUP_FAILURE")
    if not all(1<=x[2]["steps"]<=3 for x in kids): raise AssertionError("MUTATION_STEP_RANGE_FAILURE")
    if not all(dsl3.validate_strategy(x[0]) for x in kids): raise AssertionError("DSL3_OFFSPRING_FAILURE")
    print("V57_V433_QD_VARIATION_ENGINE_V1_SELF_CHECK=PASS|OPERATORS=10|MUTATION_STEPS=1_TO_3|RECIPE_MUTATION=PASS|CANONICAL_RECOMPILE=PASS|DETERMINISTIC=PASS|UNIQUE_OFFSPRING=20|CONDITION_COUNT=1_TO_4|LOGICS=46|MICRO_CRYPTO_ONLY=PASS|RISK=ATR_RR_TIME_STOP|HOLDOUT=UNREAD|ORDERS=DISABLED")
if __name__=="__main__": self_check()
