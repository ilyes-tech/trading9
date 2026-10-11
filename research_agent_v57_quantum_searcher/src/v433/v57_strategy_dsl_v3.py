import copy
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve()
V433=HERE.parent
if str(V433) not in sys.path:
    sys.path.insert(0,str(V433))

import v57_strategy_dsl_v2 as v2

CORE_OPS={"COND","AND","OR","K_OF_N"}
NARY_OPS={"XOR","XNOR","NAND","NOR","MAJORITY","SUPERMAJORITY","UNANIMOUS"}
COUNT_OPS={"EXACT_K_OF_N","AT_MOST_K_OF_N"}
UNARY_OPS={"NOT","EDGE_RISING","EDGE_FALLING","PERSIST_N","RECENT_WITHIN_N"}
SEQUENCE_OPS={"THEN_WITHIN_N","THREE_STAGE_WITHIN_N"}
SUPPORTED_OPS=CORE_OPS|NARY_OPS|COUNT_OPS|UNARY_OPS|SEQUENCE_OPS

def canonical_json(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def sha256_obj(x):
    return hashlib.sha256(canonical_json(x).encode()).hexdigest()

def _sort_children(children):
    return sorted(children,key=canonical_json)

def _dedup_sorted(children):
    seen={}
    for child in children:
        seen[canonical_json(child)]=child
    return [seen[k] for k in sorted(seen)]

def _children(node,op,min_n=1,exact_n=None,sort=False,dedup=False):
    raw=node.get("children")
    if not isinstance(raw,list):
        raise ValueError("BAD_CHILDREN:"+op)
    xs=[normalize_node(x) for x in raw]
    if exact_n is not None and len(xs)!=int(exact_n):
        raise ValueError("BAD_CHILD_COUNT:"+op)
    if len(xs)<int(min_n):
        raise ValueError("BAD_CHILD_COUNT:"+op)
    if dedup:
        xs=_dedup_sorted(xs)
    elif sort:
        xs=_sort_children(xs)
    return xs

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
        children=_children(node,op,min_n=1,sort=True,dedup=True)
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
    if op=="NOT":
        child=normalize_node(node.get("child"))
        if child.get("op")=="NOT":
            return child["child"]
        return {"op":"NOT","child":child}
    if op in ("EDGE_RISING","EDGE_FALLING"):
        return {"op":op,"child":normalize_node(node.get("child"))}
    if op in ("PERSIST_N","RECENT_WITHIN_N"):
        n=int(node.get("n",0))
        if n<1:
            raise ValueError("BAD_N:"+op)
        child=normalize_node(node.get("child"))
        if op=="PERSIST_N" and n==1:
            return child
        return {"op":op,"n":n,"child":child}
    if op in NARY_OPS:
        children=_children(node,op,min_n=2,sort=True,dedup=False)
        return {"op":op,"children":children}
    if op in COUNT_OPS:
        children=_children(node,op,min_n=2,sort=True,dedup=False)
        k=int(node.get("k",-1))
        if not 0<=k<=len(children):
            raise ValueError("BAD_K:"+op)
        return {"op":op,"k":k,"children":children}
    if op=="THEN_WITHIN_N":
        children=_children(node,op,exact_n=2)
        n=int(node.get("n",0))
        if n<1:
            raise ValueError("BAD_N:"+op)
        return {"op":op,"n":n,"children":children}
    if op=="THREE_STAGE_WITHIN_N":
        children=_children(node,op,exact_n=3)
        n_ab=int(node.get("n_ab",0))
        n_bc=int(node.get("n_bc",0))
        if n_ab<1 or n_bc<1:
            raise ValueError("BAD_N:"+op)
        return {"op":op,"n_ab":n_ab,"n_bc":n_bc,"children":children}
    raise ValueError("UNSUPPORTED_OP:"+op)

def strategy_payload(strategy):
    d=copy.deepcopy(strategy)
    d.pop("strategy_id",None)
    return d

def strategy_id(strategy):
    return sha256_obj(strategy_payload(strategy))

def validate_strategy(strategy):
    if not isinstance(strategy,dict):
        raise ValueError("STRATEGY_NOT_DICT")
    if strategy.get("schema_version")!=3 or strategy.get("kind")!="V57_STRATEGY_DSL_V3":
        raise ValueError("BAD_STRATEGY_HEADER")
    market=strategy.get("market")
    if not isinstance(market,dict):
        raise ValueError("BAD_MARKET")
    for key in ("symbol","timeframe","side"):
        if not market.get(key):
            raise ValueError("MARKET_MISSING:"+key)
    execution=strategy.get("execution")
    if not isinstance(execution,dict) or execution.get("orders_allowed") is not False:
        raise ValueError("ORDERS_MUST_BE_DISABLED")
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

def from_v2_strategy(strategy):
    v2.validate_strategy(strategy)
    d=copy.deepcopy(strategy)
    d.pop("strategy_id",None)
    d["schema_version"]=3
    d["kind"]="V57_STRATEGY_DSL_V3"
    d["signal"]=normalize_node(d["signal"])
    d.setdefault("legacy",{})
    d["legacy"]=copy.deepcopy(d["legacy"])
    d["legacy"]["source_dsl"]="V2"
    return finalize_strategy(d)

def from_v1_candidate(candidate,side):
    return from_v2_strategy(v2.from_v1_candidate(candidate,side))

def self_check():
    a={"op":"COND","condition":{"x":1}}
    b={"op":"COND","condition":{"x":2}}
    c={"op":"COND","condition":{"x":3}}
    assert normalize_node({"op":"NOT","child":{"op":"NOT","child":a}})==a
    assert normalize_node({"op":"K_OF_N","k":1,"children":[a,b]})["op"]=="OR"
    assert normalize_node({"op":"K_OF_N","k":2,"children":[a,b]})["op"]=="AND"
    q=normalize_node({"op":"THEN_WITHIN_N","n":3,"children":[b,a]})
    assert q["children"][0]==b and q["children"][1]==a
    q3=normalize_node({"op":"THREE_STAGE_WITHIN_N","n_ab":2,"n_bc":4,"children":[a,b,c]})
    assert q3["children"]==[a,b,c]
    base={"family":"volatility","feature":"BOLLINGER_WIDTH","lookback":2,"parameters":{"window":10,"multiplier":3.0},"threshold_quantile":0.4,"transform":"BELOW"}
    old={"market":"XAUUSD","timeframe":"M5","signal_logic":"K_OF_N","conditions":[base],"risk_model":{},"candidate_id":"legacy"}
    s=from_v1_candidate(old,"SHORT")
    assert s["signal"]["op"]=="COND"
    assert validate_strategy(s)
    print("V57_V433_STRATEGY_DSL_V3_SELF_CHECK=PASS|OPS=%d|V2_COMPAT=PASS|SEQUENCE_ORDER=PASS|ORDERS=DISABLED"%len(SUPPORTED_OPS))

if __name__=="__main__":
    self_check()
