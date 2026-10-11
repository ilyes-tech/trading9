import copy
import hashlib
import json
import math

CORE_OPS={"COND","AND","OR","K_OF_N"}

def canonical_json(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def sha256_obj(x):
    return hashlib.sha256(canonical_json(x).encode()).hexdigest()

def _dedup_sorted(children):
    seen={}
    for child in children:
        key=canonical_json(child)
        seen[key]=child
    return [seen[k] for k in sorted(seen)]

def normalize_node(node):
    if not isinstance(node,dict):
        raise ValueError("NODE_NOT_DICT")
    op=str(node.get("op",""))
    if op=="COND":
        cond=copy.deepcopy(node.get("condition"))
        if not isinstance(cond,dict):
            raise ValueError("COND_MISSING_CONDITION")
        return {"op":"COND","condition":cond}
    if op in ("AND","OR"):
        raw=node.get("children")
        if not isinstance(raw,list) or not raw:
            raise ValueError("BAD_CHILDREN:"+op)
        children=[]
        for child in raw:
            c=normalize_node(child)
            if c.get("op")==op:
                children.extend(c["children"])
            else:
                children.append(c)
        children=_dedup_sorted(children)
        if len(children)==1:
            return children[0]
        return {"op":op,"children":children}
    if op=="K_OF_N":
        raw=node.get("children")
        if not isinstance(raw,list) or not raw:
            raise ValueError("BAD_CHILDREN:K_OF_N")
        children=_dedup_sorted([normalize_node(x) for x in raw])
        n=len(children)
        k=int(node.get("k",math.ceil(n/2.0)))
        if not 1<=k<=n:
            raise ValueError("BAD_K_OF_N")
        if n==1:
            return children[0]
        if k==1:
            return normalize_node({"op":"OR","children":children})
        if k==n:
            return normalize_node({"op":"AND","children":children})
        return {"op":"K_OF_N","k":k,"children":children}
    raise ValueError("UNSUPPORTED_CORE_OP:"+op)

def v1_signal_node(candidate):
    conditions=candidate.get("conditions")
    if not isinstance(conditions,list) or not conditions:
        raise ValueError("BAD_V1_CONDITIONS")
    children=[{"op":"COND","condition":copy.deepcopy(c)} for c in conditions]
    logic=str(candidate.get("signal_logic"))
    if logic=="AND":
        node={"op":"AND","children":children}
    elif logic=="OR":
        node={"op":"OR","children":children}
    elif logic=="K_OF_N":
        node={"op":"K_OF_N","k":int(math.ceil(len(children)/2.0)),"children":children}
    else:
        raise ValueError("BAD_V1_SIGNAL_LOGIC:"+logic)
    return normalize_node(node)

def strategy_payload(strategy):
    d=copy.deepcopy(strategy)
    d.pop("strategy_id",None)
    return d

def strategy_id(strategy):
    return sha256_obj(strategy_payload(strategy))

def validate_strategy(strategy):
    if not isinstance(strategy,dict):
        raise ValueError("STRATEGY_NOT_DICT")
    if strategy.get("schema_version")!=2 or strategy.get("kind")!="V57_STRATEGY_DSL_V2":
        raise ValueError("BAD_STRATEGY_HEADER")
    market=strategy.get("market")
    if not isinstance(market,dict):
        raise ValueError("BAD_MARKET")
    for key in ("symbol","timeframe","side"):
        if not market.get(key):
            raise ValueError("MARKET_MISSING:"+key)
    ri=strategy.get("research_integrity")
    if not isinstance(ri,dict):
        raise ValueError("BAD_RESEARCH_INTEGRITY")
    for key in ("holdout_read","holdout_evaluated","september_2026_data_accessed","real_orders_allowed","demo_orders_allowed"):
        if ri.get(key) is not False:
            raise ValueError("RESEARCH_INTEGRITY_VIOLATION:"+key)
    signal=normalize_node(strategy.get("signal"))
    if signal!=strategy.get("signal"):
        raise ValueError("SIGNAL_NOT_CANONICAL")
    sid=strategy.get("strategy_id")
    if sid is not None and sid!=strategy_id(strategy):
        raise ValueError("STRATEGY_ID_MISMATCH")
    return True

def finalize_strategy(strategy):
    d=copy.deepcopy(strategy)
    d.pop("strategy_id",None)
    d["signal"]=normalize_node(d["signal"])
    d["strategy_id"]=strategy_id(d)
    validate_strategy(d)
    return d

def from_v1_candidate(candidate,side):
    if not isinstance(candidate,dict):
        raise ValueError("V1_CANDIDATE_NOT_DICT")
    d={
        "schema_version":2,
        "kind":"V57_STRATEGY_DSL_V2",
        "market":{
            "symbol":candidate.get("market"),
            "timeframe":candidate.get("timeframe"),
            "side":str(side)
        },
        "signal":v1_signal_node(candidate),
        "risk":copy.deepcopy(candidate.get("risk_model",{})),
        "execution":{"mode":"RESEARCH_ONLY","orders_allowed":False},
        "portfolio":{"enabled":False},
        "research_integrity":{
            "holdout_authorized":False,
            "holdout_read":False,
            "holdout_evaluated":False,
            "september_2026_data_accessed":False,
            "real_orders_allowed":False,
            "demo_orders_allowed":False
        },
        "legacy":{
            "candidate_id":candidate.get("candidate_id"),
            "signal_logic":candidate.get("signal_logic")
        }
    }
    return finalize_strategy(d)

def self_check():
    base={"family":"volatility","feature":"BOLLINGER_WIDTH","lookback":2,"parameters":{"window":10,"multiplier":3.0},"threshold_quantile":0.4,"transform":"BELOW"}
    c1={"market":"XAUUSD","timeframe":"M5","signal_logic":"K_OF_N","conditions":[base],"risk_model":{},"candidate_id":"legacy"}
    s1=from_v1_candidate(c1,"SHORT")
    assert s1["signal"]["op"]=="COND"
    a={"op":"COND","condition":{"x":1}}
    b={"op":"COND","condition":{"x":2}}
    assert normalize_node({"op":"AND","children":[b,a,a]})==normalize_node({"op":"AND","children":[a,b]})
    assert normalize_node({"op":"K_OF_N","k":1,"children":[a,b]})["op"]=="OR"
    assert validate_strategy(s1)
    print("V57_V433_STRATEGY_DSL_V2_SELF_CHECK=PASS|CORE_OPS=4|V1_COMPAT=PASS|CANONICALIZATION=PASS")

if __name__=="__main__":
    self_check()
