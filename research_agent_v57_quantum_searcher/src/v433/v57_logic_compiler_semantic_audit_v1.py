from pathlib import Path
import hashlib
import json
import sys
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
PKG=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_logic_registry_compiler_v1 as compiler
import v57_strategy_dsl_v3 as dsl3
import v57_strategy_signal_engine_v4 as engine4

ENGINE="V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V1"
EXPECTED_COMPILER_SHA256="91ef192d5b7d312febd9c13d4a0e0247b2381765ee76e96374ba8daac63954a9"
EXPECTED_CONTRACT_SHA256="429146c7fff8ea0e1baae6e862c6d03ef0d7795018731f259decb30f0b16c349"
EXPECTED_V4_SHA256="d1485519c09f7c963796a6001ad9c29393dcbc06d498ba116bfb34cc41a10484"
EXPECTED_MASK_FREEZE_SHA256="ed48bab4cd597a651ec87b4dd3679d9bfc5c0ef87cc6a8214a61c1ae62692c9b"

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _verify_upstream():
    expected={
        V433/"v57_logic_registry_compiler_v1.py":EXPECTED_COMPILER_SHA256,
        PKG/"config/v433/V57_V433_LOGIC_COMPILER_CONTRACT_V1.json":EXPECTED_CONTRACT_SHA256,
        V433/"v57_strategy_signal_engine_v4.py":EXPECTED_V4_SHA256,
        PKG/"config/v433/V57_V433_MASK_CACHE_FREEZE_V1.json":EXPECTED_MASK_FREEZE_SHA256,
    }
    for p,h in expected.items():
        actual=_sha256(p)
        if actual!=h:
            raise RuntimeError("UPSTREAM_HASH_MISMATCH:"+str(p)+":"+actual)

def _cond(name):
    return compiler.condition_node({"family":"semantic_audit","feature":name,"transform":"LEVEL","threshold_quantile":0.5})

class _Store:
    def __init__(self,masks):
        self.masks={k:np.asarray(v,dtype=bool) for k,v in masks.items()}
    def condition_mask(self,cache,condition,sec,train_mask,market=None,context_id=None):
        name=str(condition["feature"])
        if name not in self.masks:
            raise KeyError("UNKNOWN_TEST_MASK:"+name)
        return self.masks[name].copy(),0.0

def _segments(time,sec):
    t=np.asarray(time,dtype=np.int64)
    start=np.zeros(len(t),dtype=bool)
    if len(t):
        start[0]=True
    if len(t)>1:
        start[1:]=(t[1:]-t[:-1])!=int(sec)
    return np.cumsum(start)-1

def _edge_rising(x,time,sec):
    x=np.asarray(x,dtype=bool)
    seg=_segments(time,sec)
    out=np.zeros(len(x),dtype=bool)
    for i in range(1,len(x)):
        if seg[i]==seg[i-1] and x[i] and not x[i-1]:
            out[i]=True
    return out

def _edge_falling(x,time,sec):
    x=np.asarray(x,dtype=bool)
    seg=_segments(time,sec)
    out=np.zeros(len(x),dtype=bool)
    for i in range(1,len(x)):
        if seg[i]==seg[i-1] and (not x[i]) and x[i-1]:
            out[i]=True
    return out

def _persist(x,time,sec,n):
    x=np.asarray(x,dtype=bool)
    seg=_segments(time,sec)
    out=np.zeros(len(x),dtype=bool)
    run=0
    last=-1
    for i,v in enumerate(x):
        if i==0 or seg[i]!=last:
            run=0
        run=run+1 if v else 0
        out[i]=run>=int(n)
        last=seg[i]
    return out

def _recent(x,time,sec,n):
    x=np.asarray(x,dtype=bool)
    seg=_segments(time,sec)
    out=np.zeros(len(x),dtype=bool)
    for i in range(len(x)):
        lo=max(0,i-int(n)+1)
        for j in range(lo,i+1):
            if seg[j]==seg[i] and x[j]:
                out[i]=True
                break
    return out

def _then(a,b,time,sec,n):
    a=np.asarray(a,dtype=bool)
    b=np.asarray(b,dtype=bool)
    seg=_segments(time,sec)
    out=np.zeros(len(a),dtype=bool)
    for i in range(len(a)):
        if not b[i]:
            continue
        lo=max(0,i-int(n))
        for j in range(lo,i):
            if seg[j]==seg[i] and a[j]:
                out[i]=True
                break
    return out

def _eval(ast,masks,time):
    cache={"time":np.asarray(time,dtype=np.int64)}
    tm=np.ones(len(time),dtype=bool)
    thresholds={}
    out=engine4._eval_node(cache,ast,60,tm,"TEST",_Store(masks),"SEMANTIC_AUDIT|M1",thresholds)
    return np.asarray(out,dtype=bool)

def _check(name,children,params,expected,masks,time):
    ast=compiler.compile_logic(name,children,**params)
    normalized=dsl3.normalize_node(ast)
    if ast!=normalized:
        raise AssertionError("NON_CANONICAL_AST:"+name)
    got=_eval(ast,masks,time)
    exp=np.asarray(expected,dtype=bool)
    if got.shape!=exp.shape or not np.array_equal(got,exp):
        diff=np.flatnonzero(got!=exp)
        raise AssertionError("SEMANTIC_MISMATCH:"+name+":DIFF="+",".join(map(str,diff[:20])))
    return ast

def run_audit():
    _verify_upstream()
    time=np.array([0,60,120,180,600,660,720,780],dtype=np.int64)

    # Full 3-input truth table: 000,001,010,011,100,101,110,111.
    A=np.array([0,0,0,0,1,1,1,1],dtype=bool)
    B=np.array([0,0,1,1,0,0,1,1],dtype=bool)
    C=np.array([0,1,0,1,0,1,0,1],dtype=bool)

    # Separate temporal patterns with a deliberate time gap between rows 3 and 4.
    T=np.array([0,1,1,0,1,1,0,0],dtype=bool)
    U=np.array([0,0,1,1,1,0,1,1],dtype=bool)

    masks={"A":A,"B":B,"C":C,"T":T,"U":U}
    a,b,c,t,u=_cond("A"),_cond("B"),_cond("C"),_cond("T"),_cond("U")
    checks={}

    votes=A.astype(int)+B.astype(int)+C.astype(int)
    direct_cases={
        "AND":([a,b],{},A&B),
        "OR":([a,b],{},A|B),
        "XOR":([a,b],{},np.logical_xor(A,B)),
        "XNOR":([a,b],{},np.logical_not(np.logical_xor(A,B))),
        "NAND":([a,b],{},np.logical_not(A&B)),
        "NOR":([a,b],{},np.logical_not(A|B)),
        "NOT":([a],{},np.logical_not(A)),
        "PERSIST_N":([t],{"n":2},_persist(T,time,60,2)),
        "RECENT_WITHIN_N":([t],{"n":2},_recent(T,time,60,2)),
        "EDGE_RISING":([t],{},_edge_rising(T,time,60)),
        "EDGE_FALLING":([t],{},_edge_falling(T,time,60)),
        "K_OF_N":([a,b,c],{"k":2},votes>=2),
        "MAJORITY":([a,b,c],{},votes>=2),
        "SUPERMAJORITY":([a,b,c],{},votes>=2),
        "UNANIMOUS":([a,b,c],{},votes==3),
        "EXACT_K_OF_N":([a,b,c],{"k":2},votes==2),
        "AT_MOST_K_OF_N":([a,b,c],{"k":1},votes<=1),
    }
    for name,(children,params,expected) in direct_cases.items():
        checks[name]=_check(name,children,params,expected,masks,time)

    macro_cases={
        "A_AND_NOT_B":([a,b],{},A & np.logical_not(B)),
        "A_OR_NOT_B":([a,b],{},A | np.logical_not(B)),
        "EXACTLY_ONE":([a,b,c],{},votes==1),
        "AT_LEAST_ONE":([a,b,c],{},votes>=1),
        "NONE":([a,b,c],{},votes==0),
        "IMPLICATION":([a,b],{},np.logical_not(A)|B),
        "EQUIVALENCE":([a,b],{},A==B),
        "A_BEFORE_B_WITHIN_N":([t,u],{"n":2},_then(T,U,time,60,2)),
        "B_AFTER_A_WITHIN_N":([t,u],{"n":2},_then(T,U,time,60,2)),
    }
    for name,(children,params,expected) in macro_cases.items():
        checks[name]=_check(name,children,params,expected,masks,time)

    if len(checks)!=26:
        raise AssertionError("BAD_COMPILE_READY_COUNT:"+str(len(checks)))
    if set(checks)!=(compiler.DIRECT|compiler.MACROS):
        raise AssertionError("COMPILE_READY_SET_MISMATCH")

    blocked_ok=0
    for name in sorted(compiler.BLOCKED):
        try:
            compiler.compile_logic(name,[a,b])
        except RuntimeError as e:
            if not str(e).startswith("SEMANTIC_CONTRACT_BLOCKED:"+name+":"):
                raise
            blocked_ok+=1
        else:
            raise AssertionError("BLOCKED_DID_NOT_FAIL:"+name)

    registry=json.loads((PKG/"config/v433/V57_V433_LOGIC_REGISTRY_V1.json").read_text())
    allnames={n for xs in registry["families"].values() for n in xs}
    unavailable=sorted(allnames-compiler.DIRECT-compiler.MACROS-compiler.BLOCKED)
    if len(unavailable)!=135:
        raise AssertionError("BAD_UNAVAILABLE_COUNT:"+str(len(unavailable)))
    unavailable_ok=0
    for name in unavailable:
        try:
            compiler.compile_logic(name,[a,b])
        except RuntimeError as e:
            if str(e)!="RUNTIME_CAPABILITY_NOT_AVAILABLE:"+name:
                raise
            unavailable_ok+=1
        else:
            raise AssertionError("UNAVAILABLE_DID_NOT_FAIL:"+name)

    try:
        compiler.compile_logic("__UNKNOWN__",[a,b])
    except ValueError as e:
        if str(e)!="UNKNOWN_LOGIC:__UNKNOWN__":
            raise
    else:
        raise AssertionError("UNKNOWN_DID_NOT_FAIL")

    temporal_names={"PERSIST_N","RECENT_WITHIN_N","EDGE_RISING","EDGE_FALLING","A_BEFORE_B_WITHIN_N","B_AFTER_A_WITHIN_N"}
    if not temporal_names<=set(checks):
        raise AssertionError("TEMPORAL_COVERAGE_MISSING")

    print("V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V1|COMPILE_READY=26|DIRECT=17|MACROS=9|SEMANTIC_PASS=26|BLOCKED_FAIL_CLOSED=%d|UNAVAILABLE_FAIL_CLOSED=%d"%(blocked_ok,unavailable_ok))
    print("V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V1=PASS|TRUTH_TABLES=PASS|TEMPORAL_SEGMENT_AWARE=PASS|DSL3_CANONICAL=PASS|V4_EXECUTION=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

if __name__=="__main__":
    run_audit()
