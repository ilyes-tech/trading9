from pathlib import Path
import hashlib
import json
import sys
import numpy as np

HERE=Path(__file__).resolve()
SRC=HERE.parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

import v57_fold_signal_adapter_v1 as adapter
import v57_candidate_signal_engine_v1 as engine

def canonical_json(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def condition_key(condition):
    return hashlib.sha256(canonical_json(condition).encode()).hexdigest()

def finite_stats(series,mask):
    x=np.asarray(series,dtype=float)
    m=np.asarray(mask,dtype=bool)
    if x.ndim!=1 or m.shape!=x.shape:
        raise ValueError("BAD_VALIDITY_INPUT_SHAPE")
    g=m&np.isfinite(x)
    n=int(g.sum())
    total=int(m.sum())
    if n==0:
        return {
            "rows":total,
            "finite_count":0,
            "finite_ratio":0.0,
            "min":None,
            "max":None,
            "variance":None,
            "unique_count":0,
            "degenerate":True
        }
    v=x[g]
    lo=float(np.min(v))
    hi=float(np.max(v))
    var=float(np.var(v))
    uniq=int(np.unique(v).size)
    return {
        "rows":total,
        "finite_count":n,
        "finite_ratio":float(n/max(1,total)),
        "min":lo,
        "max":hi,
        "variance":var,
        "unique_count":uniq,
        "degenerate":bool(uniq<=1 or hi==lo)
    }

def probe_condition(ctx,condition):
    series=engine.condition_series(
        ctx["v57_cache"],
        condition,
        ctx["sec"],
        ctx["market"]
    )
    series=np.asarray(series,dtype=float)
    n=len(series)
    if n!=len(ctx["tf_time"]):
        raise ValueError("VALIDITY_SERIES_LENGTH_MISMATCH")
    folds=[]
    no_finite=False
    degenerate=False
    for i in range(len(adapter.v56.POL["folds"])):
        train,valid=adapter.fold_masks(ctx,i)
        ts=finite_stats(series,train)
        vs=finite_stats(series,valid)
        if ts["finite_count"]==0:
            no_finite=True
        if ts["degenerate"]:
            degenerate=True
        folds.append({
            "fold_index":i,
            "train":ts,
            "valid":vs
        })
    all_stats=finite_stats(series,np.ones(n,dtype=bool))
    status="NO_FINITE_TRAIN_VALUES" if no_finite else ("DEGENERATE" if degenerate else "USABLE")
    return {
        "condition_key":condition_key(condition),
        "condition":condition,
        "status":status,
        "usable":bool(not no_finite),
        "all":all_stats,
        "folds":folds
    }

def candidate_precheck(ctx,candidate):
    rows=[]
    usable=True
    for condition in candidate["conditions"]:
        r=probe_condition(ctx,condition)
        rows.append(r)
        if not r["usable"]:
            usable=False
    return {
        "candidate_id":candidate.get("candidate_id"),
        "market":candidate["market"],
        "timeframe":candidate["timeframe"],
        "usable":bool(usable),
        "reject_reason":None if usable else "NO_FINITE_TRAIN_VALUES",
        "conditions":rows
    }

def self_check():
    root=Path("research_agent_v57_quantum_searcher")
    ready=root/"work/autopilot_v432/shadow_ready"
    files=sorted(ready.glob("*.json"))
    if not files:
        raise RuntimeError("NO_READY_BUNDLES_FOR_SELF_CHECK")
    contexts={}
    checked=0
    for p in files:
        z=json.loads(p.read_text())
        c=z["candidate"]
        k=(c["market"],c["timeframe"])
        if k not in contexts:
            contexts[k]=adapter.prepare_context(*k)
        r=candidate_precheck(contexts[k],c)
        if not r["usable"]:
            raise RuntimeError("FALSE_REJECT_READY_BUNDLE:"+str(p))
        checked+=1
    print("V57_V433_VALIDITY_MATRIX_V1_SELF_CHECK=PASS|READY_CHECKED="+str(checked)+"|FALSE_REJECTS=0")

if __name__=="__main__":
    self_check()
