import copy
import v57_constrained_generator_v3_2 as C
import v57_qd_orchestrator_engine_v438_v1 as O
import v57_search_replay_v371_v1 as R
import v57_auto_deep_validator_v3_8 as D
ENGINE="V57_JARVIS_ADAPTIVE_SEARCH_V3_10_2"
PARENT_SID="c4b28473eadd2a868b05be4bc96db52c40fcf96e204739c4811b3add03cfc7c4"
def parent():
 s,m=C.generate({"market":"XAUUSD","timeframe":"M15","side":"SHORT","families":["momentum","trend"]},1,574382,27)[0]
 if s["strategy_id"]!=PARENT_SID: raise RuntimeError("PARENT_SID_MISMATCH")
 return s
def variants():
 p=parent(); out=[]; seen={PARENT_SID}
 def add(tag,fn):
  s=copy.deepcopy(p); fn(s); s=C.G.dsl3.finalize_strategy(s); sid=s["strategy_id"]
  if sid not in seen: seen.add(sid); out.append((tag,s))
 c0=lambda s:s["signal"]["children"][0]["child"]["condition"]
 c1=lambda s:s["signal"]["children"][1]["condition"]
 for q in (0.2,0.3,0.5,0.6): add("UO_Q_"+str(q),lambda s,q=q:c0(s).__setitem__("threshold_quantile",q))
 for x in (4,8,12,14): add("UO_LB_"+str(x),lambda s,x=x:c0(s).__setitem__("lookback",x))
 for ps in C.G._registry()["momentum"]["ULTIMATE_OSCILLATOR"]["parameter_sets"]: add("UO_PS_"+"_".join(map(str,ps)),lambda s,ps=ps:c0(s)["parameters"].__setitem__("parameter_set",ps))
 for q in (0.1,0.2,0.4,0.5): add("MDI_Q_"+str(q),lambda s,q=q:c1(s).__setitem__("threshold_quantile",q))
 for x in (24,32,64,96): add("MDI_LB_"+str(x),lambda s,x=x:c1(s).__setitem__("lookback",x))
 for w in C.G._registry()["trend"]["ADX"]["windows"]: add("MDI_W_"+str(w),lambda s,w=w:c1(s)["parameters"].__setitem__("window",w))
 for rr in C.G.legacy_gen.U["risk_models"]["rr"]: add("RR_"+str(rr),lambda s,rr=rr:s["risk"].__setitem__("rr",rr))
 for ts in C.G.legacy_gen.U["risk_models"]["time_stop_bars"]["M15"]: add("TS_"+str(ts),lambda s,ts=ts:s["risk"].__setitem__("time_stop_bars",ts))
 for am in C.G.legacy_gen.U["risk_models"]["atr_multipliers"]: add("ATR_M_"+str(am),lambda s,am=am:s["risk"].__setitem__("atr_multiplier",am))
 return out
def run():
 ctx=O.base.adapter2.prepare_context("XAUUSD","M15"); rows=[]
 for i,(tag,s) in enumerate(variants()):
  item={"strategy":s,"meta":{"market":"XAUUSD","timeframe":"M15"},"parent_strategy_id":PARENT_SID,"lineage":{"kind":ENGINE,"parent_strategy_id":PARENT_SID,"variant":tag}}
  r=O.evaluate_item(item,ENGINE,i,contexts={("XAUUSD","M15"):ctx},stores={})
  row={"tag":tag,"strategy_id":s["strategy_id"],"status":r["status"],"exact_pass":False}
  if r["status"]=="ERROR": raise RuntimeError("EVALUATION_ERROR:"+str(r.get("error")))
  if r["status"]=="EVALUATED" and r["result"].get("exact_pass"):
   row["exact_pass"]=True; q=R.evaluate_strategy(ctx,s,O.signal6.bitcache.MaskBitsetCache()); d=D.validate_dsl3(s,ctx,q); row["deep_status"]=d["status"]; row["deep"]=d.get("deep")
   rows.append(row)
   if d["status"]=="DEEP_PASS": return {"engine":ENGINE,"status":"DEEP_PASS_FOUND","winner":s,"variant":tag,"rows":rows,"orders_allowed":False,"holdout_allowed":False}
  else: rows.append(row)
 return {"engine":ENGINE,"status":"SEARCH_BUDGET_EXHAUSTED","rows":rows,"orders_allowed":False,"holdout_allowed":False}
