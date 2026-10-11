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

import v57_logic_registry_compiler_v1 as compiler1
import v57_logic_registry_compiler_v2 as compiler
import v57_logic_compiler_semantic_audit_v1 as audit1
import v57_strategy_dsl_v3 as dsl3
import v57_strategy_signal_engine_v4 as engine4

ENGINE="V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V2"
EXPECTED_COMPILER_V2_SHA256="a5f1dcd7d557dac35940bbdcf0faffcdcc6ed460f97cf0e28aa183c0fbf37077"
EXPECTED_COMPILER_V1_SHA256="91ef192d5b7d312febd9c13d4a0e0247b2381765ee76e96374ba8daac63954a9"
EXPECTED_AUDIT_V1_SHA256="b6fc25286a09c6a21bf935754d6c17008128c710c926c57860355c2a5abcb72b"
EXPECTED_EXPANSION_CONTRACT_SHA256="acf6c960a8de3134a99d56b9720b73469be1706503fff8cdc2b2d0d1575fcbbe"
EXPECTED_COMPILER_FREEZE_V1_SHA256="04e2d34ccc578827c7b1fe504fb304bbbf557b3455ad059adb3b32c890de96fe"
EXPECTED_DSL3_SHA256="8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b"
EXPECTED_V4_SHA256="d1485519c09f7c963796a6001ad9c29393dcbc06d498ba116bfb34cc41a10484"

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _verify_upstream():
    expected={
        V433/"v57_logic_registry_compiler_v2.py":EXPECTED_COMPILER_V2_SHA256,
        V433/"v57_logic_registry_compiler_v1.py":EXPECTED_COMPILER_V1_SHA256,
        V433/"v57_logic_compiler_semantic_audit_v1.py":EXPECTED_AUDIT_V1_SHA256,
        PKG/"config/v433/V57_V433_RUNTIME_CAPABILITY_EXPANSION_CONTRACT_V1.json":EXPECTED_EXPANSION_CONTRACT_SHA256,
        PKG/"config/v433/V57_V433_LOGIC_COMPILER_FREEZE_V1.json":EXPECTED_COMPILER_FREEZE_V1_SHA256,
        V433/"v57_strategy_dsl_v3.py":EXPECTED_DSL3_SHA256,
        V433/"v57_strategy_signal_engine_v4.py":EXPECTED_V4_SHA256,
    }
    for p,h in expected.items():
        actual=_sha256(p)
        if actual!=h:
            raise RuntimeError("UPSTREAM_HASH_MISMATCH:"+str(p)+":"+actual)

def _cond(name):
    return compiler.condition_node({"family":"semantic_audit_v2","feature":name,"transform":"LEVEL","threshold_quantile":0.5})

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

def _three(a,b,c,time,sec,n_ab,n_bc):
    stage_b=_then(a,b,time,sec,n_ab)
    return _then(stage_b,c,time,sec,n_bc)

def _eval(ast,masks,time):
    cache={"time":np.asarray(time,dtype=np.int64)}
    tm=np.ones(len(time),dtype=bool)
    thresholds={}
    out=engine4._eval_node(cache,ast,60,tm,"TEST",_Store(masks),"SEMANTIC_AUDIT_V2|M1",thresholds)
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

def _baseline_delegation(a,b,c,t,u):
    samples={
        "AND":([a,b],{}),"OR":([a,b],{}),"XOR":([a,b],{}),"XNOR":([a,b],{}),
        "NAND":([a,b],{}),"NOR":([a,b],{}),"NOT":([a],{}),
        "PERSIST_N":([t],{"n":2}),"RECENT_WITHIN_N":([t],{"n":2}),
        "EDGE_RISING":([t],{}),"EDGE_FALLING":([t],{}),
        "K_OF_N":([a,b,c],{"k":2}),"MAJORITY":([a,b,c],{}),
        "SUPERMAJORITY":([a,b,c],{}),"UNANIMOUS":([a,b,c],{}),
        "EXACT_K_OF_N":([a,b,c],{"k":2}),"AT_MOST_K_OF_N":([a,b,c],{"k":1}),
        "A_AND_NOT_B":([a,b],{}),"A_OR_NOT_B":([a,b],{}),"EXACTLY_ONE":([a,b,c],{}),
        "AT_LEAST_ONE":([a,b,c],{}),"NONE":([a,b,c],{}),"IMPLICATION":([a,b],{}),
        "EQUIVALENCE":([a,b],{}),"A_BEFORE_B_WITHIN_N":([t,u],{"n":2}),
        "B_AFTER_A_WITHIN_N":([t,u],{"n":2}),
    }
    if len(samples)!=26:
        raise AssertionError("BASELINE_SAMPLE_COUNT")
    for name,(children,params) in samples.items():
        old=compiler1.compile_logic(name,children,**params)
        new=compiler.compile_logic(name,children,**params)
        if old!=new:
            raise AssertionError("BASELINE_DELEGATION_MISMATCH:"+name)
    return len(samples)

def _expect_value_error(label,fn,prefix):
    try:
        fn()
    except ValueError as e:
        if not str(e).startswith(prefix):
            raise AssertionError(label+":WRONG_ERROR:"+str(e))
    else:
        raise AssertionError(label+":DID_NOT_FAIL")

def run_audit():
    _verify_upstream()

    # Re-run the frozen V1 semantic oracle first.
    audit1.run_audit()

    time=np.array([0,60,120,180,240,600,660,720,780,840,900],dtype=np.int64)
    A=np.array([0,0,0,0,1,1,1,1,0,1,0],dtype=bool)
    B=np.array([0,0,1,1,0,0,1,1,1,0,1],dtype=bool)
    C=np.array([0,1,0,1,0,1,0,1,1,1,0],dtype=bool)

    # Deliberate gap between rows 4 and 5; temporal references must never cross it.
    T=np.array([1,0,0,1,0,1,0,0,1,0,0],dtype=bool)
    U=np.array([0,1,0,0,1,0,1,0,0,1,0],dtype=bool)
    V=np.array([0,0,1,0,0,0,0,1,0,0,1],dtype=bool)
    W=np.array([0,0,0,0,0,0,0,0,0,1,0],dtype=bool)

    masks={"A":A,"B":B,"C":C,"T":T,"U":U,"V":V,"W":W}
    a,b,c,t,u,v,w=(_cond(x) for x in ("A","B","C","T","U","V","W"))

    baseline_ok=_baseline_delegation(a,b,c,t,u)

    votes=A.astype(int)+B.astype(int)+C.astype(int)
    then_tu=_then(T,U,time,60,2)
    three_tuv=_three(T,U,V,time,60,2,2)

    cases={
        "PRIMARY_PLUS_FILTER":([a,b],{},A&B),
        "PRIMARY_PLUS_CONFIRM":([a,b],{},A&B),
        "PRIMARY_PLUS_VETO":([a,b],{},A&np.logical_not(B)),
        "REGIME_PLUS_TRIGGER":([a,b],{},A&B),
        "REGIME_PLUS_TRIGGER_PLUS_VETO":([a,b,c],{},A&B&np.logical_not(C)),
        "MULTI_GATE":([a,b,c],{},A&B&C),
        "SETUP_PLUS_TRIGGER":([t,u],{"n":2},then_tu),
        "SETUP_PLUS_TRIGGER_PLUS_CONFIRM":([t,u,v],{"n":2},three_tuv),
        "STATE_MACHINE_2_STAGE":([t,u],{"n":2},then_tu),
        "STATE_MACHINE_3_STAGE":([t,u,v],{"n":2},three_tuv),
        "A_THEN_B":([t,u],{"n":2},then_tu),
        "B_THEN_A":([t,u],{"n":2},_then(U,T,time,60,2)),
        "A_THEN_B_THEN_C":([t,u,v],{"n":2},three_tuv),
        "SETUP_TRIGGER_CONFIRM":([t,u,v],{"n":2},three_tuv),
        "SETUP_TRIGGER_CONFIRM_VETO":([t,u,v,w],{"n":2},three_tuv&np.logical_not(W)),
        "CONSECUTIVE_N":([t],{"n":2},_persist(T,time,60,2)),
        "MIN_DURATION_N":([t],{"n":2},_persist(T,time,60,2)),
        "MAX_AGE_N":([t],{"n":2},_recent(T,time,60,2)),
        "EVENT_WITHIN_N":([t],{"n":2},_recent(T,time,60,2)),
        "QUORUM_VOTE":([a,b,c],{"k":2},votes>=2),
    }
    if set(cases)!=compiler.NEW_MACROS or len(cases)!=20:
        raise AssertionError("NEW_MACRO_CASE_SET_MISMATCH")

    checks={}
    for name,(children,params,expected) in cases.items():
        checks[name]=_check(name,children,params,expected,masks,time)

    if np.array_equal(
        _eval(checks["A_THEN_B"],masks,time),
        _eval(checks["B_THEN_A"],masks,time)
    ):
        raise AssertionError("SEQUENCE_DIRECTION_NOT_OBSERVABLY_DISTINCT")

    q3=checks["A_THEN_B_THEN_C"]
    if q3.get("n_ab")!=2 or q3.get("n_bc")!=2 or "n" in q3:
        raise AssertionError("THREE_STAGE_WINDOW_ENCODING_BAD")

    blocked_ok=0
    try:
        compiler.compile_logic("ALL_BUT_ONE",[a,b])
    except RuntimeError as e:
        if not str(e).startswith("SEMANTIC_CONTRACT_BLOCKED:ALL_BUT_ONE:"):
            raise
        blocked_ok=1
    else:
        raise AssertionError("BLOCKED_DID_NOT_FAIL:ALL_BUT_ONE")

    registry=json.loads((PKG/"config/v433/V57_V433_LOGIC_REGISTRY_V1.json").read_text())
    allnames={n for xs in registry["families"].values() for n in xs}
    unavailable=sorted(allnames-compiler.BASE_READY-compiler.NEW_MACROS-compiler.BLOCKED)
    if len(unavailable)!=118:
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

    _expect_value_error("MISSING_N",lambda:compiler.compile_logic("A_THEN_B",[t,u]),"MISSING_PARAM:n")
    _expect_value_error("BAD_N",lambda:compiler.compile_logic("A_THEN_B",[t,u],n=0),"BAD_PARAM:n")
    _expect_value_error("BAD_K_LOW",lambda:compiler.compile_logic("QUORUM_VOTE",[a,b,c],k=0),"BAD_PARAM:k")
    _expect_value_error("BAD_K_HIGH",lambda:compiler.compile_logic("QUORUM_VOTE",[a,b,c],k=4),"BAD_PARAM:k")
    _expect_value_error("EXTRA_PARAM",lambda:compiler.compile_logic("PRIMARY_PLUS_FILTER",[a,b],x=1),"UNEXPECTED_PARAMS:")

    try:
        compiler.compile_logic("__UNKNOWN__",[a,b])
    except ValueError as e:
        if str(e)!="UNKNOWN_LOGIC:__UNKNOWN__":
            raise
    else:
        raise AssertionError("UNKNOWN_DID_NOT_FAIL")

    if len(compiler.BASE_READY)!=26 or len(compiler.NEW_MACROS)!=20 or len(compiler.BLOCKED)!=1:
        raise AssertionError("CAPABILITY_COUNTS")
    semantic_pass=baseline_ok+len(checks)
    if semantic_pass!=46:
        raise AssertionError("SEMANTIC_PASS_COUNT:"+str(semantic_pass))

    print("V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V2|COMPILE_READY=46|BASELINE_DELEGATION=26|NEW_MACROS=20|SEMANTIC_PASS=46|BLOCKED_FAIL_CLOSED=%d|UNAVAILABLE_FAIL_CLOSED=%d"%(blocked_ok,unavailable_ok))
    print("V57_V433_LOGIC_COMPILER_SEMANTIC_AUDIT_V2=PASS|V1_ORACLE=PASS|TRUTH_TABLES=PASS|SEQUENCE_DIRECTION=PASS|THREE_STAGE_WINDOWS=PASS|TEMPORAL_SEGMENT_AWARE=PASS|PARAM_FAIL_CLOSED=PASS|DSL3_CANONICAL=PASS|V4_EXECUTION=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

if __name__=="__main__":
    run_audit()
