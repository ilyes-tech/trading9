from pathlib import Path
import copy,hashlib,json,math,sys
import numpy as np
from scipy.stats import qmc
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_candidate_schema_v1 as schema
import v57_screening_generator_v1 as legacy_gen
import v57_strategy_dsl_v3 as dsl3
import v57_logic_registry_compiler_v2 as compiler
import v57_feature_resolver_v2 as resolver
ENGINE="V57_V433_NATIVE_STRATEGY_GENERATOR_V1"
DIM=48
MAX_CONDITIONS=4
N_DOMAIN=(2,3,5,8)
EXPECTED={"runtime_freeze":"2c572b23a1386a898fe57029beec4cbfa82487120e12d9973ae7cb4b31229714","runtime_v2":"52b0aecdaf68a3968611db6f9b8cfec240efcff0fc257b67b50fcdb59165cc76","resolver_v2":"598391917542f5acda6a86408af64db4367e649336e5359f095fb781c64c2ee9","registry":"0e8c762a44a0699de02f7b53e408276e5326f60120cab38c1a65819f980f0cee","universe":"b6c48fc932c989363ff57028a7cb99ad0f2b1bb2588cec491859d73a31ee8cdf","compiler":"a5f1dcd7d557dac35940bbdcf0faffcdcc6ed460f97cf0e28aa183c0fbf37077","compiler_freeze":"d4cd7977dcd713af29eaa3dcca274e1ae284f605d0815fe54577c1928cbd9306","dsl3":"8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b","legacy_generator":"de801fcb26668fbc00b4cff2696821958b670d4221aca6d19107864be18ddfdd","replay_freeze":"b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626"}
NEW_FEATURES=(("momentum","STOCHASTIC"),("momentum","ROC"),("momentum","CCI"),("momentum","WILLIAMS_R"),("momentum","ULTIMATE_OSCILLATOR"),("momentum","FISHER_TRANSFORM"),("trend","SMA"),("trend","EMA"),("trend","ADX"),("trend","PLUS_DI"),("trend","MINUS_DI"),("volatility","ATR"),("volatility","NATR"),("volume","CMF"),("volume","MFI"),("volume","VWAP_DISTANCE"),("time","weekday_sin"),("time","weekday_cos"))
NO_PARAM_FEATURES={("volume","VWAP_DISTANCE"),("time","weekday_sin"),("time","weekday_cos")}
REGISTRY_ALIAS={("momentum","FISHER_TRANSFORM"):("momentum","FISHER"),("trend","PLUS_DI"):("trend","ADX"),("trend","MINUS_DI"):("trend","ADX")}
READY=tuple(sorted(set(compiler.BASE_READY)|set(compiler.NEW_MACROS)))
UNARY=set("NOT PERSIST_N RECENT_WITHIN_N EDGE_RISING EDGE_FALLING CONSECUTIVE_N MIN_DURATION_N MAX_AGE_N EVENT_WITHIN_N".split())
BINARY=set("A_AND_NOT_B A_OR_NOT_B IMPLICATION EQUIVALENCE A_BEFORE_B_WITHIN_N B_AFTER_A_WITHIN_N PRIMARY_PLUS_FILTER PRIMARY_PLUS_CONFIRM PRIMARY_PLUS_VETO REGIME_PLUS_TRIGGER SETUP_PLUS_TRIGGER STATE_MACHINE_2_STAGE A_THEN_B B_THEN_A".split())
TERNARY=set("REGIME_PLUS_TRIGGER_PLUS_VETO SETUP_PLUS_TRIGGER_PLUS_CONFIRM STATE_MACHINE_3_STAGE A_THEN_B_THEN_C SETUP_TRIGGER_CONFIRM".split())
QUATERNARY={"SETUP_TRIGGER_CONFIRM_VETO"}
VAR_MIN1=set("AND OR K_OF_N AT_LEAST_ONE NONE".split())
VAR_MIN2=set("XOR XNOR NAND NOR MAJORITY SUPERMAJORITY UNANIMOUS EXACT_K_OF_N AT_MOST_K_OF_N EXACTLY_ONE MULTI_GATE QUORUM_VOTE".split())
N_PARAM=set("PERSIST_N RECENT_WITHIN_N A_BEFORE_B_WITHIN_N B_AFTER_A_WITHIN_N SETUP_PLUS_TRIGGER STATE_MACHINE_2_STAGE A_THEN_B B_THEN_A SETUP_PLUS_TRIGGER_PLUS_CONFIRM STATE_MACHINE_3_STAGE A_THEN_B_THEN_C SETUP_TRIGGER_CONFIRM SETUP_TRIGGER_CONFIRM_VETO CONSECUTIVE_N MIN_DURATION_N MAX_AGE_N EVENT_WITHIN_N".split())
K_POSITIVE={"K_OF_N","QUORUM_VOTE"}
K_ZERO_OK={"EXACT_K_OF_N","AT_MOST_K_OF_N"}
REG_PATH=ROOT/"config/V57_FEATURE_REGISTRY_V1.json"
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _ensure():
    paths={"runtime_freeze":ROOT/"config/v433/V57_V433_SEARCH_RUNTIME_V2_FREEZE_V1.json","runtime_v2":V433/"v57_search_runtime_v2.py","resolver_v2":V433/"v57_feature_resolver_v2.py","registry":REG_PATH,"universe":ROOT/"config/V57_SEARCH_UNIVERSE_V1.json","compiler":V433/"v57_logic_registry_compiler_v2.py","compiler_freeze":ROOT/"config/v433/V57_V433_LOGIC_COMPILER_FREEZE_V2.json","dsl3":V433/"v57_strategy_dsl_v3.py","legacy_generator":SRC/"v57_screening_generator_v1.py","replay_freeze":ROOT/"config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json"}
    got={k:H(v) for k,v in paths.items()}
    if got!=EXPECTED: raise RuntimeError("NATIVE_GENERATOR_ANCHOR_MISMATCH:"+str(got))
    rf=json.loads(paths["runtime_freeze"].read_text())
    if rf.get("status")!="FROZEN_VALIDATED_RUNTIME_BASELINE" or rf.get("next_stage")!="V433_NATIVE_STRATEGY_GENERATOR_V1": raise RuntimeError("RUNTIME_FREEZE_STATE_MISMATCH")
    if rf.get("scope",{}).get("new_v433_features_generated_natively") is not False: raise RuntimeError("RUNTIME_SCOPE_CHANGED")
    replay_freeze=json.loads(paths["replay_freeze"].read_text())
    for z in list(replay_freeze.get("anchors",{}).values())+[replay_freeze.get("component",{})]:
        if z.get("path") and H(ROOT/z["path"])!=z["sha256"]: raise RuntimeError("FROZEN_ANCHOR_CHANGED:"+z["path"])
    if len(READY)!=46: raise RuntimeError("READY_COUNT_CHANGED:"+str(len(READY)))
    if set(compiler.BLOCKED)!={"ALL_BUT_ONE"}: raise RuntimeError("BLOCKED_SET_CHANGED")
    if set(NEW_FEATURES)!=set(resolver.NEW_FEATURES): raise RuntimeError("NEW_FEATURE_SET_MISMATCH")
    groups=UNARY|BINARY|TERNARY|QUATERNARY|VAR_MIN1|VAR_MIN2
    if groups!=set(READY): raise RuntimeError("ARITY_CLASSIFICATION_MISMATCH:"+str(sorted(set(READY)^groups)))
    if len(legacy_gen.BASE_FEATURES)!=18 or len(legacy_gen.CRYPTO_FEATURES)!=8: raise RuntimeError("LEGACY_FEATURE_POOL_CHANGED")
    return True
def _registry():
    _ensure(); return json.loads(REG_PATH.read_text())["families"]
def _rows(n,seed):
    n=int(n)
    if n<1: return np.empty((0,DIM),dtype=float)
    m=int(math.ceil(math.log2(n)))
    return qmc.Sobol(d=DIM,scramble=True,seed=int(seed)).random_base2(m)[:n]
def feature_pool(market):
    _ensure(); base=tuple(legacy_gen.BASE_FEATURES)+NEW_FEATURES
    if market in legacy_gen.CRYPTO: base=base+tuple(legacy_gen.CRYPTO_FEATURES)
    if len(base)!=len(set(base)): raise RuntimeError("FEATURE_POOL_DUPLICATE")
    return base
def _new_feature_parameters(family,feature,row,j):
    reg=_registry(); pair=(family,feature)
    if pair in NO_PARAM_FEATURES: return {}
    if pair==("momentum","ULTIMATE_OSCILLATOR"):
        vals=legacy_gen.pick(reg["momentum"]["ULTIMATE_OSCILLATOR"]["parameter_sets"],row[j%len(row)])
        return {"parameter_set":[int(x) for x in vals]}
    rfam,rfeat=REGISTRY_ALIAS.get(pair,pair)
    windows=reg[rfam][rfeat]["windows"]
    return {"window":int(legacy_gen.pick(windows,row[j%len(row)]))}
def condition_for_feature(family,feature,row,offset):
    tr=legacy_gen.pick(legacy_gen.U["transforms"],row[(offset+1)%len(row)]); lookback=legacy_gen.pick(legacy_gen.U["lookbacks"],row[(offset+2)%len(row)]); q=legacy_gen.pick(legacy_gen.U["threshold_quantiles"],row[(offset+3)%len(row)])
    if (family,feature) in resolver.NEW_FEATURES: params=_new_feature_parameters(family,feature,row,offset+4)
    else: params=legacy_gen.feature_parameters(family,feature,row,offset+4)
    return {"family":family,"feature":feature,"transform":tr,"lookback":lookback,"threshold_quantile":q,"parameters":params}
def condition_from_row(market,row,offset):
    family,feature=legacy_gen.pick(feature_pool(market),row[offset%len(row)])
    return condition_for_feature(family,feature,row,offset)
def _allowed_counts(name):
    if name in UNARY: return (1,)
    if name in BINARY: return (2,)
    if name in TERNARY: return (3,)
    if name in QUATERNARY: return (4,)
    if name in VAR_MIN1: return (1,2,3,4)
    if name in VAR_MIN2: return (2,3,4)
    raise RuntimeError("ARITY_NOT_CLASSIFIED:"+name)
def _logic_params(name,n,row,index):
    x=float(row[(40+int(index))%len(row)])
    if name in N_PARAM: return {"n":int(legacy_gen.pick(N_DOMAIN,x))}
    if name in K_POSITIVE: return {"k":int(legacy_gen.pick(tuple(range(1,n+1)),x))}
    if name in K_ZERO_OK: return {"k":int(legacy_gen.pick(tuple(range(0,n+1)),x))}
    return {}
def _compile_logic(name,conditions,row,index):
    counts=_allowed_counts(name); n=int(legacy_gen.pick(counts,row[3%len(row)])); children=[compiler.condition_node(c) for c in conditions[:n]]; params=_logic_params(name,n,row,index); node=compiler.compile_logic(name,children,**params); return node,n,params
def build_strategy(row,index):
    _ensure(); market=legacy_gen.pick(schema.MARKETS,row[0]); timeframe=legacy_gen.pick(schema.TIMEFRAMES,row[1]); side="LONG" if float(row[2])<0.5 else "SHORT"; conditions=[condition_from_row(market,row,4+i*6) for i in range(MAX_CONDITIONS)]; risk=legacy_gen.risk_from_row(row,28,timeframe); logic=READY[int(index)%len(READY)]; signal,nchildren,params=_compile_logic(logic,conditions,row,index)
    strategy={"schema_version":3,"kind":"V57_STRATEGY_DSL_V3","market":{"symbol":market,"timeframe":timeframe,"side":side},"signal":signal,"risk":copy.deepcopy(risk),"execution":{"mode":"RESEARCH_ONLY","orders_allowed":False},"portfolio":{"enabled":False},"research_integrity":{"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"real_orders_allowed":False,"demo_orders_allowed":False},"legacy":{"source_dsl":"NATIVE_V433","generator":ENGINE,"search_logic":logic,"search_logic_params":copy.deepcopy(params),"search_child_count":int(nchildren),"search_index":int(index)}}
    strategy=dsl3.finalize_strategy(strategy); meta={"index":int(index),"market":market,"timeframe":timeframe,"side":side,"logic":logic,"logic_params":params,"children":int(nchildren),"conditions":conditions}
    return strategy,meta
def generate(n,seed=574331,start=0):
    _ensure(); n=int(n); start=int(start)
    if n<0 or start<0: raise ValueError("BAD_GENERATE_RANGE")
    rows=_rows(start+n,seed)[start:start+n]
    return [build_strategy(row,start+i) for i,row in enumerate(rows)]
def _validate_new_condition(c):
    reg=_registry(); pair=(c["family"],c["feature"]); p=c["parameters"]
    if pair in NO_PARAM_FEATURES:
        if p!={}: raise AssertionError("NO_PARAM_FEATURE_HAS_PARAMS:"+str(pair))
        return
    if pair==("momentum","ULTIMATE_OSCILLATOR"):
        allowed={tuple(x) for x in reg["momentum"]["ULTIMATE_OSCILLATOR"]["parameter_sets"]}
        if set(p)!={"parameter_set"} or tuple(p["parameter_set"]) not in allowed: raise AssertionError("BAD_UO_PARAMS")
        return
    rfam,rfeat=REGISTRY_ALIAS.get(pair,pair); allowed=set(reg[rfam][rfeat]["windows"])
    if set(p)!={"window"} or p["window"] not in allowed: raise AssertionError("BAD_WINDOW_PARAMS:"+str(pair)+":"+str(p))
def self_check():
    _ensure(); resolver.self_check(); rows=_rows(46,57433101); built=[build_strategy(rows[i],i) for i in range(46)]; names=[m["logic"] for _,m in built]
    if tuple(names)!=READY: raise AssertionError("LOGIC_COVERAGE_MISMATCH")
    ids=[s["strategy_id"] for s,_ in built]
    if len(set(ids))!=46: raise AssertionError("STRATEGY_ID_COLLISION")
    for s,m in built:
        dsl3.validate_strategy(s)
        if s["execution"]["orders_allowed"] is not False: raise AssertionError("ORDERS_ENABLED")
        ri=s["research_integrity"]
        if any(ri[k] is not False for k in ("holdout_read","holdout_evaluated","september_2026_data_accessed","real_orders_allowed","demo_orders_allowed")): raise AssertionError("RESEARCH_INTEGRITY_VIOLATION")
    frows=_rows(18,57433102)
    forced=[]
    for i,(family,feature) in enumerate(NEW_FEATURES):
        c=condition_for_feature(family,feature,frows[i],0); _validate_new_condition(c); forced.append((c["family"],c["feature"]))
    if set(forced)!=set(NEW_FEATURES): raise AssertionError("NEW18_COVERAGE_MISMATCH")
    if len(feature_pool("XAUUSD"))!=36 or len(feature_pool("EURUSD"))!=36: raise AssertionError("NONCRYPTO_POOL_COUNT")
    if len(feature_pool("BTCUSD"))!=44 or len(feature_pool("ETHUSD"))!=44: raise AssertionError("CRYPTO_POOL_COUNT")
    if any(f=="crypto_microstructure" for f,_ in feature_pool("XAUUSD")): raise AssertionError("MICROSTRUCTURE_LEAK")
    s0,m0=build_strategy(rows[0],0); s1,m1=build_strategy(rows[0],0)
    if s0!=s1 or m0!=m1: raise AssertionError("NONDETERMINISTIC_BUILD")
    if compiler.capability("ALL_BUT_ONE")!="SEMANTIC_CONTRACT_BLOCKED": raise AssertionError("BLOCKED_FAIL_CLOSED_LOST")
    unavailable=set(compiler._REGISTRY_NAMES)-set(READY)-set(compiler.BLOCKED)
    if len(unavailable)!=118: raise AssertionError("UNAVAILABLE_COUNT_CHANGED")
    print("V57_V433_NATIVE_STRATEGY_GENERATOR_V1_SELF_CHECK=PASS|LEGACY_BASE=18|NEW_FEATURES=18|NONCRYPTO_POOL=36|CRYPTO_POOL=44|MICRO_CRYPTO_ONLY=PASS|COMPILE_READY=46|LOGIC_COVERAGE=46|UNIQUE_IDS=46|NEW18_PARAM_DOMAINS=PASS|DETERMINISTIC=PASS|BLOCKED=1|UNAVAILABLE=118|DSL3=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")
if __name__=="__main__": self_check()
