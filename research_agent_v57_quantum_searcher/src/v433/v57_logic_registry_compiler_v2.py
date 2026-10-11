from pathlib import Path
import hashlib
import json
import sys

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
PKG=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_strategy_dsl_v3 as dsl3
import v57_logic_registry_compiler_v1 as v1

ENGINE="V57_V433_LOGIC_REGISTRY_COMPILER_V2"
CONTRACT_PATH=PKG/"config/v433/V57_V433_RUNTIME_CAPABILITY_EXPANSION_CONTRACT_V1.json"
CONTRACT_SHA256="acf6c960a8de3134a99d56b9720b73469be1706503fff8cdc2b2d0d1575fcbbe"
V1_SHA256="91ef192d5b7d312febd9c13d4a0e0247b2381765ee76e96374ba8daac63954a9"

BASE_READY=set(v1.DIRECT)|set(v1.MACROS)
NEW_MACROS=set("""
PRIMARY_PLUS_FILTER PRIMARY_PLUS_CONFIRM PRIMARY_PLUS_VETO
REGIME_PLUS_TRIGGER REGIME_PLUS_TRIGGER_PLUS_VETO MULTI_GATE
SETUP_PLUS_TRIGGER SETUP_PLUS_TRIGGER_PLUS_CONFIRM
STATE_MACHINE_2_STAGE STATE_MACHINE_3_STAGE
A_THEN_B B_THEN_A A_THEN_B_THEN_C
SETUP_TRIGGER_CONFIRM SETUP_TRIGGER_CONFIRM_VETO
CONSECUTIVE_N MIN_DURATION_N MAX_AGE_N EVENT_WITHIN_N
QUORUM_VOTE
""".split())
BLOCKED={"ALL_BUT_ONE"}

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _contract():
    if _sha256(V433/"v57_logic_registry_compiler_v1.py")!=V1_SHA256:
        raise RuntimeError("V1_COMPILER_HASH_MISMATCH")
    if not CONTRACT_PATH.is_file():
        raise RuntimeError("EXPANSION_CONTRACT_MISSING:"+str(CONTRACT_PATH))
    h=_sha256(CONTRACT_PATH)
    if h!=CONTRACT_SHA256:
        raise RuntimeError("EXPANSION_CONTRACT_HASH_MISMATCH:"+h)
    z=json.loads(CONTRACT_PATH.read_text())
    e=z["expansion"]
    if set(e["new_exact_macros"])!=NEW_MACROS:
        raise RuntimeError("EXPANSION_MACRO_SET_MISMATCH")
    if int(e["new_exact_macro_count"])!=20:
        raise RuntimeError("EXPANSION_MACRO_COUNT_MISMATCH")
    if int(e["compile_ready_target"])!=46:
        raise RuntimeError("EXPANSION_READY_COUNT_MISMATCH")
    if set(e["semantic_blocked_after_expansion"])!=BLOCKED:
        raise RuntimeError("EXPANSION_BLOCKED_SET_MISMATCH")
    if int(e["runtime_capability_not_available_after_expansion"])!=118:
        raise RuntimeError("EXPANSION_UNAVAILABLE_COUNT_MISMATCH")
    return z

_CONTRACT=_contract()
_REGISTRY_NAMES=set()
for xs in json.loads((PKG/"config/v433/V57_V433_LOGIC_REGISTRY_V1.json").read_text())["families"].values():
    _REGISTRY_NAMES.update(xs)

def capability(logic):
    name=str(logic)
    if name in BASE_READY:
        return v1.capability(name)
    if name in NEW_MACROS:
        return "SAFE_AST_MACRO_V2"
    if name in BLOCKED:
        return "SEMANTIC_CONTRACT_BLOCKED"
    if name in _REGISTRY_NAMES:
        return "RUNTIME_CAPABILITY_NOT_AVAILABLE"
    return "UNKNOWN_LOGIC"

def _children(children,min_n=1,max_n=None):
    if not isinstance(children,list):
        raise ValueError("CHILDREN_NOT_LIST")
    if len(children)<int(min_n):
        raise ValueError("TOO_FEW_CHILDREN")
    if max_n is not None and len(children)>int(max_n):
        raise ValueError("TOO_MANY_CHILDREN")
    return [dsl3.normalize_node(x) for x in children]

def _require_int(params,key,minimum=None,maximum=None):
    if key not in params:
        raise ValueError("MISSING_PARAM:"+key)
    v=params[key]
    if isinstance(v,bool):
        raise ValueError("BAD_PARAM:"+key)
    try:
        iv=int(v)
    except Exception as e:
        raise ValueError("BAD_PARAM:"+key) from e
    if iv!=v:
        raise ValueError("BAD_PARAM:"+key)
    if minimum is not None and iv<int(minimum):
        raise ValueError("BAD_PARAM:"+key)
    if maximum is not None and iv>int(maximum):
        raise ValueError("BAD_PARAM:"+key)
    return iv

def _no_extra_params(params,allowed):
    extra=set(params)-set(allowed)
    if extra:
        raise ValueError("UNEXPECTED_PARAMS:"+",".join(sorted(extra)))

def _new_macro(name,children,params):
    if name in ("PRIMARY_PLUS_FILTER","PRIMARY_PLUS_CONFIRM","REGIME_PLUS_TRIGGER"):
        _no_extra_params(params,())
        a,b=_children(children,2,2)
        raw={"op":"AND","children":[a,b]}
    elif name=="PRIMARY_PLUS_VETO":
        _no_extra_params(params,())
        a,b=_children(children,2,2)
        raw={"op":"AND","children":[a,{"op":"NOT","child":b}]}
    elif name=="REGIME_PLUS_TRIGGER_PLUS_VETO":
        _no_extra_params(params,())
        a,b,c=_children(children,3,3)
        raw={"op":"AND","children":[a,b,{"op":"NOT","child":c}]}
    elif name=="MULTI_GATE":
        _no_extra_params(params,())
        ch=_children(children,2)
        raw={"op":"AND","children":ch}
    elif name in ("SETUP_PLUS_TRIGGER","STATE_MACHINE_2_STAGE","A_THEN_B"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a,b=_children(children,2,2)
        raw={"op":"THEN_WITHIN_N","children":[a,b],"n":n}
    elif name=="B_THEN_A":
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a,b=_children(children,2,2)
        raw={"op":"THEN_WITHIN_N","children":[b,a],"n":n}
    elif name in ("SETUP_PLUS_TRIGGER_PLUS_CONFIRM","STATE_MACHINE_3_STAGE","A_THEN_B_THEN_C","SETUP_TRIGGER_CONFIRM"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a,b,c=_children(children,3,3)
        raw={"op":"THREE_STAGE_WITHIN_N","children":[a,b,c],"n_ab":n,"n_bc":n}
    elif name=="SETUP_TRIGGER_CONFIRM_VETO":
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a,b,c,d=_children(children,4,4)
        seq={"op":"THREE_STAGE_WITHIN_N","children":[a,b,c],"n_ab":n,"n_bc":n}
        raw={"op":"AND","children":[seq,{"op":"NOT","child":d}]}
    elif name in ("CONSECUTIVE_N","MIN_DURATION_N"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a=_children(children,1,1)[0]
        raw={"op":"PERSIST_N","child":a,"n":n}
    elif name in ("MAX_AGE_N","EVENT_WITHIN_N"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a=_children(children,1,1)[0]
        raw={"op":"RECENT_WITHIN_N","child":a,"n":n}
    elif name=="QUORUM_VOTE":
        _no_extra_params(params,("k",))
        ch=_children(children,2)
        k=_require_int(params,"k",1,len(ch))
        raw={"op":"K_OF_N","children":ch,"k":k}
    else:
        raise RuntimeError("V2_MACRO_HANDLER_MISSING:"+name)
    return dsl3.normalize_node(raw)

def compile_logic(logic,children,**params):
    name=str(logic)
    cap=capability(name)
    if name in BASE_READY:
        return v1.compile_logic(name,children,**params)
    if cap=="SAFE_AST_MACRO_V2":
        return _new_macro(name,children,params)
    if cap=="SEMANTIC_CONTRACT_BLOCKED":
        reason=_CONTRACT["expansion"]["semantic_blocked_after_expansion"][name]
        raise RuntimeError("SEMANTIC_CONTRACT_BLOCKED:"+name+":"+reason)
    if cap=="RUNTIME_CAPABILITY_NOT_AVAILABLE":
        raise RuntimeError("RUNTIME_CAPABILITY_NOT_AVAILABLE:"+name)
    raise ValueError("UNKNOWN_LOGIC:"+name)

def condition_node(condition):
    return v1.condition_node(condition)

def self_check():
    a=condition_node({"family":"test","feature":"A","transform":"LEVEL","threshold_quantile":0.25})
    b=condition_node({"family":"test","feature":"B","transform":"LEVEL","threshold_quantile":0.75})
    c=condition_node({"family":"test","feature":"C","transform":"LEVEL","threshold_quantile":0.5})
    d=condition_node({"family":"test","feature":"D","transform":"LEVEL","threshold_quantile":0.6})
    v1.self_check()
    samples={
        "PRIMARY_PLUS_FILTER":([a,b],{}),
        "PRIMARY_PLUS_CONFIRM":([a,b],{}),
        "PRIMARY_PLUS_VETO":([a,b],{}),
        "REGIME_PLUS_TRIGGER":([a,b],{}),
        "REGIME_PLUS_TRIGGER_PLUS_VETO":([a,b,c],{}),
        "MULTI_GATE":([a,b,c],{}),
        "SETUP_PLUS_TRIGGER":([a,b],{"n":3}),
        "SETUP_PLUS_TRIGGER_PLUS_CONFIRM":([a,b,c],{"n":3}),
        "STATE_MACHINE_2_STAGE":([a,b],{"n":3}),
        "STATE_MACHINE_3_STAGE":([a,b,c],{"n":3}),
        "A_THEN_B":([a,b],{"n":3}),
        "B_THEN_A":([a,b],{"n":3}),
        "A_THEN_B_THEN_C":([a,b,c],{"n":3}),
        "SETUP_TRIGGER_CONFIRM":([a,b,c],{"n":3}),
        "SETUP_TRIGGER_CONFIRM_VETO":([a,b,c,d],{"n":3}),
        "CONSECUTIVE_N":([a],{"n":3}),
        "MIN_DURATION_N":([a],{"n":3}),
        "MAX_AGE_N":([a],{"n":3}),
        "EVENT_WITHIN_N":([a],{"n":3}),
        "QUORUM_VOTE":([a,b,c],{"k":2}),
    }
    for name,(ch,pa) in samples.items():
        out=compile_logic(name,ch,**pa)
        dsl3.normalize_node(out)
    if compile_logic("A_THEN_B",[a,b],n=3)==compile_logic("B_THEN_A",[a,b],n=3):
        raise AssertionError("SEQUENCE_DIRECTION_COLLAPSED")
    try:
        compile_logic("ALL_BUT_ONE",[a,b])
    except RuntimeError as e:
        if not str(e).startswith("SEMANTIC_CONTRACT_BLOCKED:ALL_BUT_ONE:"):
            raise
    else:
        raise AssertionError("BLOCKED_DID_NOT_FAIL")
    unavailable=_REGISTRY_NAMES-BASE_READY-NEW_MACROS-BLOCKED
    if len(unavailable)!=118:
        raise AssertionError("UNAVAILABLE_COUNT:"+str(len(unavailable)))
    for name in unavailable:
        try:
            compile_logic(name,[a,b])
        except RuntimeError as e:
            if str(e)!="RUNTIME_CAPABILITY_NOT_AVAILABLE:"+name:
                raise
        else:
            raise AssertionError("UNAVAILABLE_DID_NOT_FAIL:"+name)
    if len(BASE_READY)!=26 or len(NEW_MACROS)!=20:
        raise AssertionError("CAPABILITY_COUNTS")
    print("V57_V433_LOGIC_REGISTRY_COMPILER_V2_SELF_CHECK=PASS|BASELINE=26|NEW_MACROS=20|COMPILE_READY=46|BLOCKED=1|UNAVAILABLE=118|FAIL_CLOSED=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
