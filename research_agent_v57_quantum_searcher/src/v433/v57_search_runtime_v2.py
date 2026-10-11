from pathlib import Path
import argparse,copy,hashlib,json,math,sys,time
import numpy as np
from scipy.stats import qmc
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_candidate_schema_v1 as schema
import v57_screening_generator_v1 as gen
import v57_strategy_dsl_v3 as dsl3
import v57_logic_registry_compiler_v2 as compiler
import v57_fold_signal_adapter_v2 as adapter2
import v57_strategy_signal_engine_v5 as signal5
import v57_search_replay_v1 as replay
ENGINE="V57_V433_SEARCH_RUNTIME_V2"
EXPECTED={"replay_freeze":"b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626","compiler":"a5f1dcd7d557dac35940bbdcf0faffcdcc6ed460f97cf0e28aa183c0fbf37077","compiler_freeze":"d4cd7977dcd713af29eaa3dcca274e1ae284f605d0815fe54577c1928cbd9306","generator":"de801fcb26668fbc00b4cff2696821958b670d4221aca6d19107864be18ddfdd"}
READY=tuple(sorted(set(compiler.BASE_READY)|set(compiler.NEW_MACROS)))
N_DOMAIN=(2,3,5,8)
N_PARAM=set("PERSIST_N RECENT_WITHIN_N A_BEFORE_B_WITHIN_N B_AFTER_A_WITHIN_N SETUP_PLUS_TRIGGER STATE_MACHINE_2_STAGE A_THEN_B B_THEN_A SETUP_PLUS_TRIGGER_PLUS_CONFIRM STATE_MACHINE_3_STAGE A_THEN_B_THEN_C SETUP_TRIGGER_CONFIRM SETUP_TRIGGER_CONFIRM_VETO CONSECUTIVE_N MIN_DURATION_N MAX_AGE_N EVENT_WITHIN_N".split())
K_PARAM={"K_OF_N","EXACT_K_OF_N","AT_MOST_K_OF_N","QUORUM_VOTE"}
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _ensure():
    paths={"replay_freeze":ROOT/"config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json","compiler":V433/"v57_logic_registry_compiler_v2.py","compiler_freeze":ROOT/"config/v433/V57_V433_LOGIC_COMPILER_FREEZE_V2.json","generator":SRC/"v57_screening_generator_v1.py"}
    got={k:H(v) for k,v in paths.items()}
    if got!=EXPECTED: raise RuntimeError("SEARCH_RUNTIME_ANCHOR_MISMATCH:"+str(got))
    f=json.loads(paths["replay_freeze"].read_text())
    if f.get("status")!="FROZEN_AFTER_FULL_SEMANTIC_AUDIT": raise RuntimeError("SEARCH_REPLAY_NOT_FROZEN")
    items=[f["component"]]+list(f.get("anchors",{}).values())
    for z in items:
        p=ROOT/z["path"]
        if H(p)!=z["sha256"]: raise RuntimeError("FROZEN_ANCHOR_CHANGED:"+z["path"])
    if len(READY)!=46: raise RuntimeError("COMPILE_READY_COUNT_CHANGED:"+str(len(READY)))
    if set(compiler.BLOCKED)!={"ALL_BUT_ONE"}: raise RuntimeError("BLOCKED_SET_CHANGED")
    unavailable=set(compiler._REGISTRY_NAMES)-set(READY)-set(compiler.BLOCKED)
    if len(unavailable)!=118: raise RuntimeError("UNAVAILABLE_COUNT_CHANGED:"+str(len(unavailable)))
    return True
def _rows(n,seed):
    n=int(n)
    if n<1: return np.empty((0,48),dtype=float)
    m=int(math.ceil(math.log2(n)))
    return qmc.Sobol(d=48,scramble=True,seed=int(seed)).random_base2(m)[:n]
def _base_candidate(row):
    market=gen.pick(schema.MARKETS,row[0]); tf=gen.pick(schema.TIMEFRAMES,row[1])
    conditions=[gen.condition_from_row(market,row,4+i*6) for i in range(4)]
    risk=gen.risk_from_row(row,28,tf)
    c={"market":market,"timeframe":tf,"signal_logic":"AND","conditions":conditions,"risk_model":risk,"research_integrity":{"holdout_read":False,"september_2026_data_accessed":False,"real_orders_allowed":False}}
    return schema.finalize_candidate(c)
def _params(name,nchildren,row,index):
    if name in N_PARAM:
        j=min(int(float(row[(32+index)%48])*len(N_DOMAIN)),len(N_DOMAIN)-1)
        return {"n":int(N_DOMAIN[j])}
    if name in K_PARAM:
        k=1+min(int(float(row[(33+index)%48])*int(nchildren)),int(nchildren)-1)
        return {"k":int(k)}
    return {}
def _compile(name,conditions,row,index):
    nodes=[compiler.condition_node(c) for c in conditions]
    last=None
    for n in (4,3,2,1):
        ch=nodes[:n]; pa=_params(name,n,row,index)
        try: return compiler.compile_logic(name,ch,**pa),n,pa
        except ValueError as e: last=e
    if last is not None: raise last
    raise RuntimeError("LOGIC_COMPILE_FAILED:"+name)
def build_strategy(row,index):
    c=_base_candidate(row); side="LONG" if float(row[2])<0.5 else "SHORT"; name=READY[int(index)%len(READY)]
    node,nchildren,pa=_compile(name,c["conditions"],row,int(index)); st=dsl3.from_v1_candidate(c,side); q=copy.deepcopy(st); q.pop("strategy_id",None); q["signal"]=node; q.setdefault("legacy",{}); q["legacy"]=copy.deepcopy(q["legacy"]); q["legacy"]["search_runtime"]=ENGINE; q["legacy"]["search_logic"]=name; q["legacy"]["search_logic_params"]=pa; q["legacy"]["search_child_count"]=int(nchildren); q["legacy"]["search_index"]=int(index); q=dsl3.finalize_strategy(q)
    return q,{"logic":name,"params":pa,"children":int(nchildren),"side":side,"market":c["market"],"timeframe":c["timeframe"]}
def signal_prefilter(ctx,strategy,store):
    symbol=strategy["market"]["symbol"]; tf=strategy["market"]["timeframe"]; cid=symbol+"|"+tf+"|SEARCH_REPLAY_V1"; rows=[]; ok=True
    for fi in range(3):
        train,valid=adapter2.fold_masks(ctx,fi); train=np.asarray(train,dtype=bool); valid=np.asarray(valid,dtype=bool)
        sig=signal5.strategy_signal(ctx["v57_cache"],strategy,ctx["sec"],train,symbol,store,cid); events=np.asarray(sig["signal"],dtype=bool); count=int(np.count_nonzero(events&valid)); days=float(valid.sum()*ctx["sec"]/86400.0)
        need_trades=int(replay.GATE["min_trades_per_fold"]); need_tpd=int(math.ceil(float(replay.GATE["min_active_market_tpd"])*days-1e-12)); need=max(need_trades,need_tpd); passed=bool(count>=need); ok=bool(ok and passed)
        rows.append({"fold_index":fi,"signal_events":count,"minimum_required_upper_bound":need,"valid_days":days,"pass":passed})
    return {"pass":ok,"reason":"NECESSARY_SIGNAL_DENSITY_UPPER_BOUND","folds":rows}
def _f(x,default=-1e100):
    try:
        v=float(x)
        return v if np.isfinite(v) else default
    except Exception: return default
def score(result):
    return (1 if result.get("exact_pass") else 0,_f(result.get("worst_stress_avg_bps")),_f(result.get("min_stress_pf")),_f(result.get("worst_base_avg_bps")),_f(result.get("min_base_pf")),_f(result.get("worst_drawdown_bps")),int(result.get("total_selected_trades",0)))
def _atomic_json(path,obj):
    p=Path(path); t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n"); t.replace(p)
def run(count,seed=57433,start=0,outdir=None,top=20):
    _ensure(); count=int(count); start=int(start); seed=int(seed)
    if count<1 or start<0: raise ValueError("BAD_SEARCH_RANGE")
    out=Path(outdir) if outdir else ROOT/"work/v433_search_runtime_v2"; out.mkdir(parents=True,exist_ok=True)
    tag="seed%d_start%d_count%d"%(seed,start,count); raw=out/("V433_SEARCH_"+tag+".jsonl"); state=out/("V433_SEARCH_"+tag+"_STATE.json"); topf=out/("V433_SEARCH_"+tag+"_TOP.json")
    if raw.exists() or state.exists() or topf.exists(): raise RuntimeError("OUTPUT_ALREADY_EXISTS:"+tag)
    rows=_rows(start+count,seed)[start:start+count]; ctxs={}; stores={}; records=[]; errors=rejects=evaluated=0; t0=time.time()
    for j,row in enumerate(rows):
        idx=start+j; meta={}; strategy=None; pref=None; result=None; err=None; status="ERROR"
        try:
            strategy,meta=build_strategy(row,idx); key=(meta["market"],meta["timeframe"])
            if key not in ctxs: ctxs[key]=adapter2.prepare_context(*key); stores[key]=signal5.bitcache.MaskBitsetCache()
            pref=signal_prefilter(ctxs[key],strategy,stores[key])
            if not pref["pass"]: status="PREFILTER_REJECT"; rejects+=1
            else: result=replay.evaluate_strategy(ctxs[key],strategy,stores[key]); status="EVALUATED"; evaluated+=1
        except ValueError as e:
            if str(e)=="NO_FINITE_TRAIN_VALUES":
                status="PREFILTER_REJECT"; rejects+=1; pref={"pass":False,"reason":"NO_FINITE_TRAIN_VALUES_FAIL_CLOSED","source_exception":"ValueError:NO_FINITE_TRAIN_VALUES","folds":[]}; err=None
            else:
                errors+=1; err=type(e).__name__+":"+str(e)
        except Exception as e:
            errors+=1; err=type(e).__name__+":"+str(e)
        rec={"schema_version":1,"kind":"V57_V433_SEARCH_RUNTIME_RECORD_V2","engine":ENGINE,"seed":seed,"index":idx,"status":status,"meta":meta,"strategy":strategy,"prefilter":pref,"result":result,"error":err,"research_integrity":{"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"demo_orders_allowed":False,"real_orders_allowed":False}}
        with raw.open("a") as fh: fh.write(json.dumps(rec,sort_keys=True)+"\n"); fh.flush()
        records.append(rec); _atomic_json(state,{"engine":ENGINE,"seed":seed,"start":start,"count":count,"completed":j+1,"last_index":idx,"evaluated":evaluated,"prefilter_rejects":rejects,"errors":errors,"raw":str(raw),"holdout_read":False,"orders_allowed":False})
        if (j+1)%8==0 or j+1==count: print("V57_V433_SEARCH_RUNTIME_PROGRESS|DONE=%d/%d|EVALUATED=%d|PREFILTER_REJECT=%d|ERRORS=%d"%(j+1,count,evaluated,rejects,errors),flush=True)
    ranked=[r for r in records if isinstance(r.get("result"),dict)]; ranked.sort(key=lambda r:score(r["result"]),reverse=True); _atomic_json(topf,ranked[:max(0,int(top))])
    print("V57_V433_SEARCH_RUNTIME_DONE|COUNT=%d|EVALUATED=%d|PREFILTER_REJECT=%d|ERRORS=%d|SECONDS=%.3f"%(count,evaluated,rejects,errors,time.time()-t0),flush=True); print("RAW="+str(raw),flush=True); print("STATE="+str(state),flush=True); print("TOP="+str(topf),flush=True)
    return {"count":count,"evaluated":evaluated,"prefilter_rejects":rejects,"errors":errors,"raw":str(raw),"state":str(state),"top":str(topf)}
def self_check():
    _ensure(); rows=_rows(46,5743301); built=[build_strategy(rows[i],i) for i in range(46)]; names=[m["logic"] for _,m in built]
    if tuple(names)!=READY: raise AssertionError("READY_COVERAGE_MISMATCH")
    ids=[s["strategy_id"] for s,_ in built]
    if len(set(ids))!=46: raise AssertionError("STRATEGY_ID_COLLISION")
    s0,m0=build_strategy(rows[0],0); s1,m1=build_strategy(rows[0],0)
    if s0!=s1 or m0!=m1: raise AssertionError("NONDETERMINISTIC_BUILD")
    if compiler.capability("ALL_BUT_ONE")!="SEMANTIC_CONTRACT_BLOCKED": raise AssertionError("BLOCKED_FAIL_CLOSED_LOST")
    unavailable=set(compiler._REGISTRY_NAMES)-set(READY)-set(compiler.BLOCKED)
    if len(unavailable)!=118: raise AssertionError("UNAVAILABLE_COUNT")
    sample=sorted(unavailable)[0]
    if compiler.capability(sample)!="RUNTIME_CAPABILITY_NOT_AVAILABLE": raise AssertionError("UNAVAILABLE_FAIL_CLOSED_LOST")
    print("V57_V433_SEARCH_RUNTIME_V2_SELF_CHECK=PASS|COMPILE_READY=46|COVERAGE=46|UNIQUE_IDS=46|DETERMINISTIC=PASS|BLOCKED=1|UNAVAILABLE=118|PREFILTER=NECESSARY_ONLY|CHECKPOINT=ATOMIC|HOLDOUT=UNREAD|ORDERS=DISABLED")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--count",type=int,default=0); ap.add_argument("--seed",type=int,default=57433); ap.add_argument("--start",type=int,default=0); ap.add_argument("--out"); ap.add_argument("--top",type=int,default=20); a=ap.parse_args()
    if a.count<=0: self_check()
    else: run(a.count,a.seed,a.start,a.out,a.top)
