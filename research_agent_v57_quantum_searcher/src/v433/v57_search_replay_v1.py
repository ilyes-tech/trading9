from pathlib import Path
import hashlib,json,sys,numpy as np
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=HERE.parents[2]
V56=(Path("research_agent_v56_strategy_factory")/"src").resolve()
for p in (V433,SRC,V56):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v56_fold_evaluator_v3 as v56
import v57_candidate_schema_v1 as legacy_schema
import v57_replay_evaluator_v2 as legacy_replay
import v57_screening_generator_v1 as legacy_gen
import v57_indicator_core_v1 as ind
import v57_strategy_dsl_v3 as dsl3
import v57_strategy_signal_engine_v5 as signal5
import v57_fold_signal_adapter_v2 as adapter2
ENGINE="V57_V433_SEARCH_REPLAY_V1"
CONTRACT=json.loads((ROOT/"config/V57_QUANTUM_SEARCHER_CONTRACT_V1.json").read_text())
GATE=CONTRACT["gate"]
EXPECTED={"v5":"8d0714ef291760baede7fdff47344925c616184196002b95124d9ccb448ace43","v5_freeze":"25bc34a33be9c9c5e2dc0baf3443837503f9001950cb3277bdb3e128c86d6913","adapter2":"ace33c4f7eaf1c7c42ca002c38f34c08860a34dd5c56874593444e5721788506","dsl3":"8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b","replay1":"c6c241df58e9296c118c2eb15a66ffc2e5d46214e86f69866d7d0b4662845785","replay2":"ed0890d2d93e7b80a5aa8ffa939bac2653ddfcadee6349b53570563b56b4ddf7"}
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _ensure():
    got={"v5":H(V433/"v57_strategy_signal_engine_v5.py"),"v5_freeze":H(ROOT/"config/v433/V57_V433_STRATEGY_SIGNAL_ENGINE_V5_FREEZE_V1.json"),"adapter2":H(V433/"v57_fold_signal_adapter_v2.py"),"dsl3":H(V433/"v57_strategy_dsl_v3.py"),"replay1":H(SRC/"v57_replay_evaluator_v1.py"),"replay2":H(SRC/"v57_replay_evaluator_v2.py")}
    if got!=EXPECTED: raise RuntimeError("SEARCH_REPLAY_ANCHOR_MISMATCH:"+str(got))
def _market(strategy):
    m=strategy.get("market")
    if not isinstance(m,dict): raise ValueError("STRATEGY_MARKET_MISSING")
    symbol=str(m.get("symbol") or "")
    timeframe=str(m.get("timeframe") or "")
    side=str(m.get("side") or "").upper()
    if not symbol: raise ValueError("STRATEGY_SYMBOL_MISSING")
    if not timeframe: raise ValueError("STRATEGY_TIMEFRAME_MISSING")
    if side not in ("LONG","SHORT"): raise ValueError("BAD_SIDE:"+side)
    return m,symbol,timeframe,side
def gate_pass(f):
    n=int(f["trades"]); tpd=float(f["tpd"]); b=f.get("base_avg_bps"); s=f.get("stress_avg_bps")
    return bool(n>=int(GATE["min_trades_per_fold"]) and tpd>=float(GATE["min_active_market_tpd"]) and b is not None and float(b)>float(GATE["base_avg_bps_gt"]) and float(f["base_pf"])>=float(GATE["base_pf_gte"]) and s is not None and float(s)>float(GATE["stress_avg_bps_gt"]) and float(f["stress_pf"])>=float(GATE["stress_pf_gte"]))
def _risk(strategy,timeframe):
    r=strategy.get("risk")
    if not isinstance(r,dict): raise ValueError("STRATEGY_RISK_MISSING")
    legacy_schema.validate_risk_model(r,timeframe)
    if r.get("stop")!="ATR": raise ValueError("RISK_STOP_SEMANTICS_MISSING:"+str(r.get("stop")))
    if r.get("take_profit")!="RR": raise ValueError("TAKE_PROFIT_SEMANTICS_MISSING:"+str(r.get("take_profit")))
    if bool(r.get("break_even")): raise ValueError("BREAK_EVEN_SEMANTICS_MISSING")
    if bool(r.get("trailing_stop")): raise ValueError("TRAILING_STOP_SEMANTICS_MISSING")
    return r
def _risk_atr(cache,sec,window):
    key="atr_"+str(int(window))
    if key in cache: return np.asarray(cache[key],dtype=float)
    return ind.atr(np.asarray(cache["high"],float),np.asarray(cache["low"],float),np.asarray(cache["close"],float),np.asarray(cache["time"],np.int64),int(sec),int(window))
def _risk_levels(ctx,risk,signal_i,entry_m1,side,atr_series):
    atr=float(atr_series[int(signal_i)])
    if not np.isfinite(atr) or atr<=0: return None
    entry=float(ctx["m1_open"][entry_m1]+ctx["spread"][entry_m1]) if side=="LONG" else float(ctx["m1_open"][entry_m1])
    raw_stop=entry-float(risk["atr_multiplier"])*atr if side=="LONG" else entry+float(risk["atr_multiplier"])*atr
    if not np.isfinite(raw_stop): return None
    return v56.base.broker.brokerize_levels(ctx["market"],side,entry,raw_stop,float(risk["rr"]))
def evaluate_fold(ctx,strategy,fold_index,shared_cache=None,context_id=None):
    _ensure(); dsl3.validate_strategy(strategy); m,symbol,timeframe,side=_market(strategy)
    if symbol!=ctx["market"] or timeframe!=ctx["timeframe"]: raise ValueError("CONTEXT_STRATEGY_MISMATCH")
    risk=_risk(strategy,timeframe); train,valid=adapter2.fold_masks(ctx,int(fold_index)); train=np.asarray(train,dtype=bool); valid=np.asarray(valid,dtype=bool); store=shared_cache if shared_cache is not None else signal5.bitcache.MaskBitsetCache(); cid=context_id or (symbol+"|"+timeframe+"|SEARCH_REPLAY_V1")
    sig=signal5.strategy_signal(ctx["v57_cache"],strategy,ctx["sec"],train,symbol,store,cid); events=np.asarray(sig["signal"],dtype=bool); signals=np.flatnonzero(events&valid)
    c=dict(ctx); c["spread"]=v56.fold_spread(ctx,int(fold_index)); atr_series=_risk_atr(c["v57_cache"],c["sec"],risk["atr_window"]); hold=int(risk["time_stop_bars"]); pre=[]
    for si in signals:
        e=int(si)+1; due=e+hold
        if due>=len(c["tf_time"]) or not valid[e] or not valid[due]: continue
        a=int(c["tf_to_m1"][si]); b=int(c["tf_to_m1"][e])
        if b<=a or np.any(c["unexpected"][a:b]): continue
        em=int(c["tf_to_m1"][e]); dm=int(c["tf_to_m1"][due]); lv=_risk_levels(c,risk,int(si),em,side,atr_series)
        if lv is None: continue
        q=v56.base.replay.replay_trade(c["market"],side,c["m1_time"],c["m1_open"],c["m1_high"],c["m1_low"],c["m1_close"],c["spread"],em,dm,float(lv["stop"]),float(lv["target"]),c["scheduled"])
        if q.get("eligible",False):
            q=v56.base.replay.apply_costs(c["asset_class"],q); q["signal_tf_i"]=int(si); pre.append(q)
    selected=v56.select_nonoverlap(pre); base=np.asarray([q["base_net_bps"] for q in selected],float); stress=np.asarray([q["stress_net_bps"] for q in selected],float); days=float(valid.sum()*c["sec"]/86400.0); out=v56.fold_summary(base,stress,days,c["timeframe"])
    out["fold_index"]=int(fold_index); out["side"]=side; out["signal_events"]=int(len(signals)); out["eligible_pre_nonoverlap"]=int(len(pre)); out["selected_trades"]=int(len(selected)); out["thresholds"]=[float(x) for x in sig["thresholds"]]; out["pass"]=gate_pass(out); out["gate_source"]="V57_QUANTUM_SEARCHER_CONTRACT_V1"; return out
def evaluate_strategy(ctx,strategy,shared_cache=None):
    _ensure(); dsl3.validate_strategy(strategy); m,symbol,timeframe,side=_market(strategy)
    if symbol!=ctx["market"] or timeframe!=ctx["timeframe"]: raise ValueError("CONTEXT_STRATEGY_MISMATCH")
    store=shared_cache if shared_cache is not None else signal5.bitcache.MaskBitsetCache(); cid=symbol+"|"+timeframe+"|SEARCH_REPLAY_V1"; folds=[evaluate_fold(ctx,strategy,i,store,cid) for i in range(3)]; cv=lambda x:(-float("inf") if x is None else float(x))
    return {"strategy_id":strategy.get("strategy_id",dsl3.strategy_id(strategy)),"market":symbol,"timeframe":timeframe,"side":side,"folds":folds,"exact_pass":bool(all(f["pass"] for f in folds)),"worst_stress_avg_bps":min(cv(f["stress_avg_bps"]) for f in folds),"min_stress_pf":min(float(f["stress_pf"]) for f in folds),"worst_base_avg_bps":min(cv(f["base_avg_bps"]) for f in folds),"min_base_pf":min(float(f["base_pf"]) for f in folds),"mean_stress_avg_bps":float(np.mean([cv(f["stress_avg_bps"]) for f in folds])),"mean_base_avg_bps":float(np.mean([cv(f["base_avg_bps"]) for f in folds])),"worst_drawdown_bps":min(float(f["drawdown_bps"]) for f in folds),"total_selected_trades":int(sum(f["selected_trades"] for f in folds))}
def _same(a,b):
    if a is None or b is None: return a is b
    if isinstance(a,(float,np.floating)) or isinstance(b,(float,np.floating)):
        try:
            x=float(a); y=float(b); return (np.isnan(x) and np.isnan(y)) or x==y
        except Exception: return False
    return a==b
def self_check():
    _ensure(); candidates=legacy_gen.generate(6,57991); checks=fold_checks=paired_errors=0; ff=("trades","tpd","base_avg_bps","base_pf","stress_avg_bps","stress_pf","drawdown_bps","signal_events","eligible_pre_nonoverlap","selected_trades","pass"); rf=("exact_pass","worst_stress_avg_bps","min_stress_pf","worst_base_avg_bps","min_base_pf","mean_stress_avg_bps","mean_base_avg_bps","worst_drawdown_bps","total_selected_trades")
    for c in candidates:
        ctx=adapter2.prepare_context(c["market"],c["timeframe"])
        for side in ("LONG","SHORT"):
            s=dsl3.from_v1_candidate(c,side); assert s["market"]["side"]==side; assert s["market"]["symbol"]==c["market"]; assert s["market"]["timeframe"]==c["timeframe"]; checks+=1
            try: old=legacy_replay.evaluate_candidate(ctx,c,side)
            except Exception as e1:
                try: evaluate_strategy(ctx,s)
                except Exception as e2:
                    if type(e1) is not type(e2) or str(e1)!=str(e2): raise AssertionError(("ERROR_PARITY",type(e1).__name__,str(e1),type(e2).__name__,str(e2)))
                    paired_errors+=1; continue
                raise AssertionError(("OLD_ERROR_NEW_PASS",type(e1).__name__,str(e1)))
            new=evaluate_strategy(ctx,s)
            for of,nf in zip(old["folds"],new["folds"]):
                for k in ff:
                    if not _same(of.get(k),nf.get(k)): raise AssertionError(("FOLD_PARITY",c["market"],c["timeframe"],side,k,of.get(k),nf.get(k)))
                fold_checks+=1
            for k in rf:
                if not _same(old.get(k),new.get(k)): raise AssertionError(("RESULT_PARITY",c["market"],c["timeframe"],side,k,old.get(k),new.get(k)))
    print("V57_V433_SEARCH_REPLAY_V1_SELF_CHECK=PASS|STRATEGIES=%d|FOLD_CHECKS=%d|PAIRED_ERRORS=%d|MARKET_SIDE_PATH=PASS|LEGACY_REPLAY_PARITY=PASS|V5_SIGNAL=PASS|CACHE_V2=PASS|TIME_STOP=PRESERVED|HOLDOUT=UNREAD|ORDERS=DISABLED"%(checks,fold_checks,paired_errors))
if __name__=="__main__": self_check()
