from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_qd_variation_engine_v1 as q
import v57_native_strategy_generator_v1 as gen
import v57_search_runtime_v3 as rt
import v57_strategy_dsl_v3 as dsl3
ENGINE="V57_V433_QD_VARIATION_SEMANTIC_AUDIT_V1"
EXPECTED={"variation":"21acf86faed0e833dc4aca5483d21cc9fe96cdb39c97f284c6e129a9c9bdfa87","policy":"d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f","runtime":"6d6f747e4d3c1ef3a67a2544b0de5ac783ee7bb9cbdf7aa180f30bc99bce04a0","runtime_freeze":"89c9561e7e38848ef60d5febbf5873d7580926c6328074ea6a990c91bd5dc968","replay":"4732f4e824f5af4b2942733367239fecbef8198750c0a7af6f96f68d27bf8706","replay_freeze":"b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626","signal_v5":"8d0714ef291760baede7fdff47344925c616184196002b95124d9ccb448ace43","adapter_v2":"ace33c4f7eaf1c7c42ca002c38f34c08860a34dd5c56874593444e5721788506","generator":"2d0698578dcb1e09eeb935cf96db672b8b41d55a96edd6704b03d2d93adb0afd","generator_freeze":"205f3f4f09477a4117daef21effceec61f7f6125cc00cce3df98c51e76a82dc9","dsl3":"8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b"}
PATHS={"variation":V433/"v57_qd_variation_engine_v1.py","policy":ROOT/"config/v433/V57_V433_QD_SEARCH_POLICY_V1.json","runtime":V433/"v57_search_runtime_v3.py","runtime_freeze":ROOT/"config/v433/V57_V433_SEARCH_RUNTIME_V3_FREEZE_V1.json","replay":V433/"v57_search_replay_v1.py","replay_freeze":ROOT/"config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json","signal_v5":V433/"v57_strategy_signal_engine_v5.py","adapter_v2":V433/"v57_fold_signal_adapter_v2.py","generator":V433/"v57_native_strategy_generator_v1.py","generator_freeze":ROOT/"config/v433/V57_V433_NATIVE_STRATEGY_GENERATOR_V1_FREEZE_V1.json","dsl3":V433/"v57_strategy_dsl_v3.py"}
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ensure():
    got={k:H(v) for k,v in PATHS.items()}
    if got!=EXPECTED: raise RuntimeError("QD_VARIATION_AUDIT_ANCHOR_MISMATCH:"+str(got))
    q._ensure(); rt._ensure()
    return got
def evaluate_child(strategy,ctxs,stores):
    dsl3.validate_strategy(strategy); symbol=strategy["market"]["symbol"]; tf=strategy["market"]["timeframe"]; key=(symbol,tf)
    if key not in ctxs:
        ctxs[key]=rt.adapter2.prepare_context(symbol,tf); stores[key]=rt.signal5.bitcache.MaskBitsetCache()
    try:
        pref=rt.signal_prefilter(ctxs[key],strategy,stores[key])
        if not pref["pass"]: return {"status":"PREFILTER_REJECT","reason":pref.get("reason"),"exact_pass":False,"folds":0}
        result=rt.replay.evaluate_strategy(ctxs[key],strategy,stores[key])
        if len(result.get("folds",[]))!=3: raise AssertionError("REPLAY_FOLD_COUNT_NOT_3")
        return {"status":"EVALUATED","reason":None,"exact_pass":bool(result.get("exact_pass")),"folds":3}
    except ValueError as e:
        if str(e)=="NO_FINITE_TRAIN_VALUES": return {"status":"PREFILTER_REJECT","reason":"NO_FINITE_TRAIN_VALUES_FAIL_CLOSED","exact_pass":False,"folds":0}
        raise
def main():
    anchors=ensure(); pairs=gen.generate(384,943410,0); recipes=[q.recipe_from_pair(s,m) for s,m in pairs]
    if len({s["strategy_id"] for s,m in pairs})!=384: raise AssertionError("PARENT_ID_DUPLICATION")
    ctxs={}; stores={}; operator_rows=[]
    for oi,op in enumerate(q.OPERATORS):
        found=None
        for pi,(parent,meta) in enumerate(pairs):
            seed=944100+oi*1000+pi
            try:
                r1=q.mutate_recipe(recipes[pi],op,seed,recipes); s1,m1=q.strategy_from_recipe(r1)
                r2=q.mutate_recipe(recipes[pi],op,seed,recipes); s2,m2=q.strategy_from_recipe(r2)
            except ValueError:
                continue
            if r1!=r2 or s1!=s2 or m1!=m2: raise AssertionError("NONDETERMINISTIC_OPERATOR:"+op)
            if s1["strategy_id"]==parent["strategy_id"]: raise AssertionError("OPERATOR_NO_ID_CHANGE:"+op)
            q.validate_recipe(r1); dsl3.validate_strategy(s1); ev=evaluate_child(s1,ctxs,stores)
            found={"operator":op,"parent_index":pi,"parent_strategy_id":parent["strategy_id"],"child_strategy_id":s1["strategy_id"],"market":m1["market"],"timeframe":m1["timeframe"],"side":m1["side"],"logic":m1["logic"],"condition_count":m1["children"],"status":ev["status"],"reason":ev["reason"],"exact_pass":ev["exact_pass"],"folds":ev["folds"]}; break
        if found is None: raise AssertionError("OPERATOR_NOT_SEMANTICALLY_COVERED:"+op)
        operator_rows.append(found)
    if len(operator_rows)!=10 or {x["operator"] for x in operator_rows}!=set(q.OPERATORS): raise AssertionError("OPERATOR_COVERAGE_FAILURE")
    first_by_context={}
    for i,(s,m) in enumerate(pairs):
        first_by_context.setdefault((m["market"],m["timeframe"]),i)
    expected_contexts={(m,t) for m in gen.schema.MARKETS for t in gen.schema.TIMEFRAMES}
    if set(first_by_context)!=expected_contexts: raise AssertionError("CONTEXT_COVERAGE_NOT_24:"+str(sorted(set(expected_contexts)-set(first_by_context))))
    context_rows=[]; context_ids=set()
    for ci,key in enumerate(sorted(first_by_context)):
        pi=first_by_context[key]; parent,meta=pairs[pi]; base=recipes[pi]; donors=[recipes[j] for j,(s,m) in enumerate(pairs) if m["market"]==meta["market"] and j!=pi][:64]
        made=0; attempt=0
        while made<2 and attempt<100:
            seed=946000+ci*1000+made*100+attempt; attempt+=1
            try:
                rr,ops=q.mutate_sequence(base,seed,donors); child,cm=q.strategy_from_recipe(rr)
            except ValueError:
                continue
            if child["strategy_id"]==parent["strategy_id"] or child["strategy_id"] in context_ids: continue
            context_ids.add(child["strategy_id"]); ev=evaluate_child(child,ctxs,stores); context_rows.append({"context_index":ci,"offspring_index":made,"parent_strategy_id":parent["strategy_id"],"child_strategy_id":child["strategy_id"],"market":cm["market"],"timeframe":cm["timeframe"],"side":cm["side"],"logic":cm["logic"],"condition_count":cm["children"],"operators":ops,"steps":len(ops),"status":ev["status"],"reason":ev["reason"],"exact_pass":ev["exact_pass"],"folds":ev["folds"]}); made+=1
        if made!=2: raise AssertionError("CONTEXT_OFFSPRING_SHORTFALL:"+str(key))
    if len(context_rows)!=48 or len(context_ids)!=48: raise AssertionError("CONTEXT_OFFSPRING_DEDUP_FAILURE")
    p0,m0=pairs[first_by_context[sorted(first_by_context)[0]]]; donor_pairs=[x for x in pairs if x[1]["market"]==m0["market"]][:64]; api_kids=q.generate_offspring(p0,m0,8,947001,donor_pairs); api_rows=[]
    if len(api_kids)!=8 or len({x[0]["strategy_id"] for x in api_kids})!=8: raise AssertionError("GENERATE_OFFSPRING_API_DEDUP_FAILURE")
    for child,cm,vm in api_kids:
        ev=evaluate_child(child,ctxs,stores); api_rows.append({"child_strategy_id":child["strategy_id"],"market":cm["market"],"timeframe":cm["timeframe"],"side":cm["side"],"logic":cm["logic"],"condition_count":cm["children"],"operators":vm["operators"],"steps":vm["steps"],"status":ev["status"],"reason":ev["reason"],"exact_pass":ev["exact_pass"],"folds":ev["folds"]})
    all_rows=operator_rows+context_rows+api_rows; evaluated=sum(x["status"]=="EVALUATED" for x in all_rows); rejected=sum(x["status"]=="PREFILTER_REJECT" for x in all_rows); nofinite=sum(x.get("reason")=="NO_FINITE_TRAIN_VALUES_FAIL_CLOSED" for x in all_rows); exact=sum(bool(x.get("exact_pass")) for x in all_rows)
    if evaluated<1: raise AssertionError("NO_REAL_REPLAY_EVALUATION_REACHED")
    if evaluated+rejected!=len(all_rows): raise AssertionError("UNCLASSIFIED_AUDIT_OUTCOME")
    out={"schema_version":1,"kind":ENGINE,"status":"PASS","classification":"ENGINEERING_SEMANTIC_AUDIT_ONLY_NOT_SEARCH_CANDIDATE_SET","seeds":{"parent_pool":943410,"operator_base":944100,"context_base":946000,"generate_offspring_api":947001},"anchors":anchors,"coverage":{"operators":10,"market_timeframe_contexts":24,"context_offspring":48,"generate_offspring_api":8,"total_children":len(all_rows)},"outcomes":{"evaluated":evaluated,"prefilter_reject":rejected,"no_finite_fail_closed":nofinite,"exact_pass_audit_only":exact,"unexpected_errors":0},"operator_rows":operator_rows,"context_rows":context_rows,"generate_offspring_api_rows":api_rows,"research_integrity":{"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"demo_orders_allowed":False,"real_orders_allowed":False}}
    od=ROOT/"work/v433_qd_variation_semantic_audit_v1"; od.mkdir(parents=True,exist_ok=True); target=od/"V57_V433_QD_VARIATION_SEMANTIC_AUDIT_V1.json"; temp=od/"V57_V433_QD_VARIATION_SEMANTIC_AUDIT_V1.json.tmp"
    if target.exists(): raise RuntimeError("AUDIT_OUTPUT_ALREADY_EXISTS:"+str(target))
    temp.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); temp.replace(target)
    print("V57_V433_QD_VARIATION_SEMANTIC_AUDIT_V1=PASS|OPERATORS=10|CONTEXTS=24|CONTEXT_OFFSPRING=48|API_OFFSPRING=8|TOTAL=%d|EVALUATED=%d|PREFILTER_REJECT=%d|NO_FINITE=%d|EXACT_AUDIT_ONLY=%d|ERRORS=0|HOLDOUT=UNREAD|ORDERS=DISABLED"%(len(all_rows),evaluated,rejected,nofinite,exact))
    print("AUDIT_RESULT="+str(target)); print("AUDIT_RESULT_SHA256="+H(target))
if __name__=="__main__": main()
