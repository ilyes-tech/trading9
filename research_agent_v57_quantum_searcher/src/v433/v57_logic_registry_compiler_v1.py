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

ENGINE="V57_V433_LOGIC_REGISTRY_COMPILER_V1"
CONTRACT_PATH=PKG/"config/v433/V57_V433_LOGIC_COMPILER_CONTRACT_V1.json"
CONTRACT_SHA256="429146c7fff8ea0e1baae6e862c6d03ef0d7795018731f259decb30f0b16c349"

DIRECT=set("AND OR XOR XNOR NAND NOR NOT PERSIST_N RECENT_WITHIN_N EDGE_RISING EDGE_FALLING K_OF_N MAJORITY SUPERMAJORITY UNANIMOUS EXACT_K_OF_N AT_MOST_K_OF_N".split())
MACROS=set("A_AND_NOT_B A_OR_NOT_B EXACTLY_ONE AT_LEAST_ONE NONE IMPLICATION EQUIVALENCE A_BEFORE_B_WITHIN_N B_AFTER_A_WITHIN_N".split())
BLOCKED=set("ALL_BUT_ONE A_THEN_B B_THEN_A A_THEN_B_THEN_C".split())

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _contract():
    if not CONTRACT_PATH.is_file():
        raise RuntimeError("CONTRACT_MISSING:"+str(CONTRACT_PATH))
    h=_sha256(CONTRACT_PATH)
    if h!=CONTRACT_SHA256:
        raise RuntimeError("CONTRACT_HASH_MISMATCH:"+h)
    z=json.loads(CONTRACT_PATH.read_text())
    scope=z["compiler_scope"]
    if set(scope["direct_native_ast"])!=DIRECT:
        raise RuntimeError("CONTRACT_DIRECT_MISMATCH")
    if set(scope["safe_macros"])!=MACROS:
        raise RuntimeError("CONTRACT_MACRO_MISMATCH")
    if set(scope["semantic_contract_blocked"])!=BLOCKED:
        raise RuntimeError("CONTRACT_BLOCKED_MISMATCH")
    if int(scope["compile_ready_exact"])!=26:
        raise RuntimeError("CONTRACT_READY_COUNT_MISMATCH")
    return z

_CONTRACT=_contract()
_REGISTRY_NAMES=set()
for xs in json.loads((PKG/"config/v433/V57_V433_LOGIC_REGISTRY_V1.json").read_text())["families"].values():
    _REGISTRY_NAMES.update(xs)

def capability(logic):
    name=str(logic)
    if name in DIRECT:
        return "DIRECT_NATIVE_AST"
    if name in MACROS:
        return "SAFE_AST_MACRO"
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

def _direct(name,children,params):
    if name=="NOT":
        _no_extra_params(params,())
        ch=_children(children,1,1)
        raw={"op":"NOT","child":ch[0]}
    elif name in ("EDGE_RISING","EDGE_FALLING"):
        _no_extra_params(params,())
        ch=_children(children,1,1)
        raw={"op":name,"child":ch[0]}
    elif name in ("PERSIST_N","RECENT_WITHIN_N"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        ch=_children(children,1,1)
        raw={"op":name,"child":ch[0],"n":n}
    elif name=="K_OF_N":
        _no_extra_params(params,("k",))
        ch=_children(children,1)
        k=_require_int(params,"k",1,len(ch))
        raw={"op":"K_OF_N","children":ch,"k":k}
    elif name in ("EXACT_K_OF_N","AT_MOST_K_OF_N"):
        _no_extra_params(params,("k",))
        ch=_children(children,2)
        k=_require_int(params,"k",0,len(ch))
        raw={"op":name,"children":ch,"k":k}
    elif name in ("AND","OR"):
        _no_extra_params(params,())
        ch=_children(children,1)
        raw={"op":name,"children":ch}
    elif name in ("XOR","XNOR","NAND","NOR","MAJORITY","SUPERMAJORITY","UNANIMOUS"):
        _no_extra_params(params,())
        ch=_children(children,2)
        raw={"op":name,"children":ch}
    else:
        raise RuntimeError("DIRECT_HANDLER_MISSING:"+name)
    return dsl3.normalize_node(raw)

def _macro(name,children,params):
    if name in ("A_AND_NOT_B","A_OR_NOT_B","IMPLICATION","EQUIVALENCE"):
        _no_extra_params(params,())
        a,b=_children(children,2,2)
        if name=="A_AND_NOT_B":
            raw={"op":"AND","children":[a,{"op":"NOT","child":b}]}
        elif name=="A_OR_NOT_B":
            raw={"op":"OR","children":[a,{"op":"NOT","child":b}]}
        elif name=="IMPLICATION":
            raw={"op":"OR","children":[{"op":"NOT","child":a},b]}
        else:
            raw={"op":"XNOR","children":[a,b]}
    elif name=="EXACTLY_ONE":
        _no_extra_params(params,())
        ch=_children(children,2)
        raw={"op":"EXACT_K_OF_N","children":ch,"k":1}
    elif name=="AT_LEAST_ONE":
        _no_extra_params(params,())
        ch=_children(children,1)
        raw={"op":"OR","children":ch}
    elif name=="NONE":
        _no_extra_params(params,())
        ch=_children(children,1)
        raw={"op":"NOT","child":{"op":"OR","children":ch}}
    elif name in ("A_BEFORE_B_WITHIN_N","B_AFTER_A_WITHIN_N"):
        _no_extra_params(params,("n",))
        n=_require_int(params,"n",1)
        a,b=_children(children,2,2)
        raw={"op":"THEN_WITHIN_N","children":[a,b],"n":n}
    else:
        raise RuntimeError("MACRO_HANDLER_MISSING:"+name)
    return dsl3.normalize_node(raw)

def compile_logic(logic,children,**params):
    name=str(logic)
    cap=capability(name)
    if cap=="DIRECT_NATIVE_AST":
        return _direct(name,children,params)
    if cap=="SAFE_AST_MACRO":
        return _macro(name,children,params)
    if cap=="SEMANTIC_CONTRACT_BLOCKED":
        reason=_CONTRACT["compiler_scope"]["semantic_contract_blocked"][name]
        raise RuntimeError("SEMANTIC_CONTRACT_BLOCKED:"+name+":"+reason)
    if cap=="RUNTIME_CAPABILITY_NOT_AVAILABLE":
        raise RuntimeError("RUNTIME_CAPABILITY_NOT_AVAILABLE:"+name)
    raise ValueError("UNKNOWN_LOGIC:"+name)

def condition_node(condition):
    return dsl3.normalize_node({"op":"COND","condition":dict(condition)})

def self_check():
    a=condition_node({"family":"test","feature":"A","transform":"LEVEL","threshold_quantile":0.25})
    b=condition_node({"family":"test","feature":"B","transform":"LEVEL","threshold_quantile":0.75})
    c=condition_node({"family":"test","feature":"C","transform":"LEVEL","threshold_quantile":0.5})
    samples={
        "AND":([a,b],{}),"OR":([a,b],{}),"XOR":([a,b],{}),"XNOR":([a,b],{}),
        "NAND":([a,b],{}),"NOR":([a,b],{}),"NOT":([a],{}),
        "PERSIST_N":([a],{"n":2}),"RECENT_WITHIN_N":([a],{"n":2}),
        "EDGE_RISING":([a],{}),"EDGE_FALLING":([a],{}),
        "K_OF_N":([a,b,c],{"k":2}),"MAJORITY":([a,b,c],{}),
        "SUPERMAJORITY":([a,b,c],{}),"UNANIMOUS":([a,b,c],{}),
        "EXACT_K_OF_N":([a,b,c],{"k":2}),"AT_MOST_K_OF_N":([a,b,c],{"k":1})
    }
    for name,(ch,pa) in samples.items():
        out=compile_logic(name,ch,**pa)
        dsl3.normalize_node(out)
    macro_samples={
        "A_AND_NOT_B":([a,b],{}),"A_OR_NOT_B":([a,b],{}),"EXACTLY_ONE":([a,b,c],{}),
        "AT_LEAST_ONE":([a,b],{}),"NONE":([a,b],{}),"IMPLICATION":([a,b],{}),
        "EQUIVALENCE":([a,b],{}),"A_BEFORE_B_WITHIN_N":([a,b],{"n":3}),
        "B_AFTER_A_WITHIN_N":([a,b],{"n":3})
    }
    for name,(ch,pa) in macro_samples.items():
        out=compile_logic(name,ch,**pa)
        dsl3.normalize_node(out)
    for name in sorted(BLOCKED):
        try:
            compile_logic(name,[a,b])
        except RuntimeError as e:
            if not str(e).startswith("SEMANTIC_CONTRACT_BLOCKED:"+name+":"):
                raise
        else:
            raise AssertionError("BLOCKED_DID_NOT_FAIL:"+name)
    probe=next(iter(_REGISTRY_NAMES-DIRECT-MACROS-BLOCKED))
    try:
        compile_logic(probe,[a,b])
    except RuntimeError as e:
        if str(e)!="RUNTIME_CAPABILITY_NOT_AVAILABLE:"+probe:
            raise
    else:
        raise AssertionError("UNAVAILABLE_DID_NOT_FAIL:"+probe)
    if len(DIRECT)!=17 or len(MACROS)!=9 or len(BLOCKED)!=4:
        raise AssertionError("CAPABILITY_COUNTS")
    print("V57_V433_LOGIC_REGISTRY_COMPILER_V1_SELF_CHECK=PASS|DIRECT=17|MACROS=9|COMPILE_READY=26|BLOCKED=4|FAIL_CLOSED=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
