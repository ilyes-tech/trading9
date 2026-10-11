from pathlib import Path
import hashlib
import math
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

import v57_feature_resolver_v1 as v1
import v57_indicator_core_v1 as q

CONTRACT_PATH=ROOT/"config/v433/V57_V433_MONO_CONTEXT_RUNTIME_EXPANSION_CONTRACT_V2.json"
REGISTRY_PATH=ROOT/"config/V57_FEATURE_REGISTRY_V1.json"
V1_PATH=SRC/"v57_feature_resolver_v1.py"
CORE_PATH=SRC/"v57_indicator_core_v1.py"

EXPECTED_SHA256={
    str(CONTRACT_PATH):"e4cf2187dd61c94315e029b4cd44fbec97088170bd07ae7c0c8d68fd10f1a63d",
    str(REGISTRY_PATH):"0e8c762a44a0699de02f7b53e408276e5326f60120cab38c1a65819f980f0cee",
    str(V1_PATH):"820497b91f92f87b2a8478fccb6d269c76e450ff2daa8de18f02293e78568c41",
    str(CORE_PATH):"e29861e6837c3f8483b2e8bf56c5a1ea246d836cfe9a70dd13690436f8775384",
}

NEW_FEATURES={
    ("momentum","STOCHASTIC"),
    ("momentum","ROC"),
    ("momentum","CCI"),
    ("momentum","WILLIAMS_R"),
    ("momentum","ULTIMATE_OSCILLATOR"),
    ("momentum","FISHER_TRANSFORM"),
    ("trend","SMA"),
    ("trend","EMA"),
    ("trend","ADX"),
    ("trend","PLUS_DI"),
    ("trend","MINUS_DI"),
    ("volatility","ATR"),
    ("volatility","NATR"),
    ("volume","CMF"),
    ("volume","MFI"),
    ("volume","VWAP_DISTANCE"),
    ("time","weekday_sin"),
    ("time","weekday_cos"),
}

_VERIFIED=False
_REGISTRY=None

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _ensure_contract():
    global _VERIFIED,_REGISTRY
    if _VERIFIED:
        return
    for p,h in EXPECTED_SHA256.items():
        got=_sha256(p)
        if got!=h:
            raise RuntimeError("V433_FEATURE_RESOLVER_V2_ANCHOR_MISMATCH:"+p+":"+got)
    import json
    _REGISTRY=json.loads(REGISTRY_PATH.read_text())["families"]
    _VERIFIED=True

def _parameters(condition):
    p=condition.get("parameters")
    if p is None:
        return {}
    if not isinstance(p,dict):
        raise ValueError("PARAMETERS_NOT_DICT")
    return p

def _exact_keys(p,keys,label):
    if set(p)!=set(keys):
        raise ValueError("BAD_PARAMETERS:"+label)

def _strict_int(x,label):
    if isinstance(x,bool) or not isinstance(x,(int,np.integer)):
        raise ValueError("BAD_INTEGER_PARAMETER:"+label)
    return int(x)

def _window(condition,family,registry_feature):
    _ensure_contract()
    p=_parameters(condition)
    _exact_keys(p,{"window"},condition["feature"])
    n=_strict_int(p["window"],condition["feature"]+":window")
    allowed=set(_REGISTRY[family][registry_feature]["windows"])
    if n not in allowed:
        raise ValueError("BAD_PARAMETERS:"+condition["feature"])
    return n

def _uo_parameters(condition):
    _ensure_contract()
    p=_parameters(condition)
    _exact_keys(p,{"parameter_set"},"ULTIMATE_OSCILLATOR")
    s=p["parameter_set"]
    if not isinstance(s,(list,tuple)) or len(s)!=3:
        raise ValueError("BAD_PARAMETERS:ULTIMATE_OSCILLATOR")
    vals=tuple(_strict_int(x,"ULTIMATE_OSCILLATOR:parameter_set") for x in s)
    allowed={tuple(x) for x in _REGISTRY["momentum"]["ULTIMATE_OSCILLATOR"]["parameter_sets"]}
    if vals not in allowed:
        raise ValueError("BAD_PARAMETERS:ULTIMATE_OSCILLATOR")
    return vals

def _no_parameters(condition):
    p=_parameters(condition)
    _exact_keys(p,set(),condition["feature"])

def _base(cache):
    v1.require(cache,"time","open","high","low","close","volume")
    return (
        np.asarray(cache["time"],dtype=np.int64),
        np.asarray(cache["open"],dtype=float),
        np.asarray(cache["high"],dtype=float),
        np.asarray(cache["low"],dtype=float),
        np.asarray(cache["close"],dtype=float),
        np.asarray(cache["volume"],dtype=float),
    )

def resolve_feature(cache,condition,sec,market=None):
    _ensure_contract()
    if not isinstance(condition,dict):
        raise ValueError("CONDITION_NOT_DICT")
    family=condition.get("family")
    feature=condition.get("feature")
    if (family,feature) not in NEW_FEATURES:
        return v1.resolve_feature(cache,condition,sec,market)
    t,o,h,l,c,v=_base(cache)
    sec=int(sec)
    if sec<1:
        raise ValueError("BAD_SEC")
    if family=="momentum" and feature=="STOCHASTIC":
        return q.stochastic(h,l,c,t,sec,_window(condition,"momentum","STOCHASTIC"))
    if family=="momentum" and feature=="ROC":
        return q.roc(c,t,sec,_window(condition,"momentum","ROC"))
    if family=="momentum" and feature=="CCI":
        return q.cci(h,l,c,t,sec,_window(condition,"momentum","CCI"))
    if family=="momentum" and feature=="WILLIAMS_R":
        return q.williams_r(h,l,c,t,sec,_window(condition,"momentum","WILLIAMS_R"))
    if family=="momentum" and feature=="ULTIMATE_OSCILLATOR":
        n1,n2,n3=_uo_parameters(condition)
        return q.ultimate_oscillator(h,l,c,t,sec,n1,n2,n3)
    if family=="momentum" and feature=="FISHER_TRANSFORM":
        return q.fisher_transform(h,l,t,sec,_window(condition,"momentum","FISHER"))
    if family=="trend" and feature=="SMA":
        return q.sma(c,t,sec,_window(condition,"trend","SMA"))
    if family=="trend" and feature=="EMA":
        return q.ema(c,t,sec,_window(condition,"trend","EMA"))
    if family=="trend" and feature in ("ADX","PLUS_DI","MINUS_DI"):
        n=_window(condition,"trend","ADX")
        ax,pdi,mdi=q.adx(h,l,c,t,sec,n)
        return {"ADX":ax,"PLUS_DI":pdi,"MINUS_DI":mdi}[feature]
    if family=="volatility" and feature=="ATR":
        return q.atr(h,l,c,t,sec,_window(condition,"volatility","ATR"))
    if family=="volatility" and feature=="NATR":
        return q.natr(h,l,c,t,sec,_window(condition,"volatility","NATR"))
    if family=="volume" and feature=="CMF":
        return q.cmf(h,l,c,v,t,sec,_window(condition,"volume","CMF"))
    if family=="volume" and feature=="MFI":
        return q.mfi(h,l,c,v,t,sec,_window(condition,"volume","MFI"))
    if family=="volume" and feature=="VWAP_DISTANCE":
        _no_parameters(condition)
        return 10000.0*(q.safe_div(c,q.vwap(h,l,c,v,t,sec))-1.0)
    if family=="time" and feature in ("weekday_sin","weekday_cos"):
        _no_parameters(condition)
        weekday=np.mod(np.floor_divide(t,86400)+3,7).astype(float)
        angle=2.0*math.pi*weekday/7.0
        return np.sin(angle) if feature=="weekday_sin" else np.cos(angle)
    raise KeyError("FEATURE_MAPPING_MISSING:"+str(family)+":"+str(feature))

def _same(a,b):
    a=np.asarray(a,dtype=float)
    b=np.asarray(b,dtype=float)
    return a.shape==b.shape and np.allclose(a,b,rtol=0.0,atol=0.0,equal_nan=True)

def _expect_fail(fn,label):
    try:
        fn()
    except Exception:
        return
    raise AssertionError("EXPECTED_FAIL:"+label)

def self_check():
    _ensure_contract()
    assert len(NEW_FEATURES)==18
    sec=60
    n=96
    t=np.arange(n,dtype=np.int64)*sec
    t[60:]+=sec*3
    x=np.arange(n,dtype=float)
    c=100.0+0.08*x+1.7*np.sin(x/3.7)
    o=c+0.25*np.sin(x/5.0)
    h=np.maximum(o,c)+0.7+0.1*np.cos(x/4.0)
    l=np.minimum(o,c)-0.6-0.1*np.sin(x/6.0)
    v=1000.0+50.0*np.sin(x/2.3)+3.0*x
    cache={"time":t,"open":o,"high":h,"low":l,"close":c,"volume":v}
    cache["obv"]=q.obv(c,v,t,sec)
    cache["vwap"]=q.vwap(h,l,c,v,t,sec)
    cache["hour_sin"]=np.sin(2.0*math.pi*np.mod(t,86400)/86400.0)
    cache["hour_cos"]=np.cos(2.0*math.pi*np.mod(t,86400)/86400.0)
    cache["trades"]=100.0+x
    tests=[
        ({"family":"momentum","feature":"STOCHASTIC","parameters":{"window":5}},q.stochastic(h,l,c,t,sec,5)),
        ({"family":"momentum","feature":"ROC","parameters":{"window":5}},q.roc(c,t,sec,5)),
        ({"family":"momentum","feature":"CCI","parameters":{"window":7}},q.cci(h,l,c,t,sec,7)),
        ({"family":"momentum","feature":"WILLIAMS_R","parameters":{"window":5}},q.williams_r(h,l,c,t,sec,5)),
        ({"family":"momentum","feature":"ULTIMATE_OSCILLATOR","parameters":{"parameter_set":[4,8,16]}},q.ultimate_oscillator(h,l,c,t,sec,4,8,16)),
        ({"family":"momentum","feature":"FISHER_TRANSFORM","parameters":{"window":5}},q.fisher_transform(h,l,t,sec,5)),
        ({"family":"trend","feature":"SMA","parameters":{"window":5}},q.sma(c,t,sec,5)),
        ({"family":"trend","feature":"EMA","parameters":{"window":5}},q.ema(c,t,sec,5)),
        ({"family":"trend","feature":"ADX","parameters":{"window":7}},q.adx(h,l,c,t,sec,7)[0]),
        ({"family":"trend","feature":"PLUS_DI","parameters":{"window":7}},q.adx(h,l,c,t,sec,7)[1]),
        ({"family":"trend","feature":"MINUS_DI","parameters":{"window":7}},q.adx(h,l,c,t,sec,7)[2]),
        ({"family":"volatility","feature":"ATR","parameters":{"window":5}},q.atr(h,l,c,t,sec,5)),
        ({"family":"volatility","feature":"NATR","parameters":{"window":5}},q.natr(h,l,c,t,sec,5)),
        ({"family":"volume","feature":"CMF","parameters":{"window":10}},q.cmf(h,l,c,v,t,sec,10)),
        ({"family":"volume","feature":"MFI","parameters":{"window":7}},q.mfi(h,l,c,v,t,sec,7)),
        ({"family":"volume","feature":"VWAP_DISTANCE","parameters":{}},10000.0*(q.safe_div(c,q.vwap(h,l,c,v,t,sec))-1.0)),
    ]
    for cond,expected in tests:
        got=resolve_feature(cache,cond,sec,"TEST")
        assert _same(got,expected),cond["feature"]
    wt=np.array([0,86400,2*86400,3*86400,4*86400,5*86400,6*86400],dtype=np.int64)
    wc={k:np.ones(7,dtype=float) for k in ("open","high","low","close","volume")}
    wc["time"]=wt
    wd=np.mod(np.floor_divide(wt,86400)+3,7).astype(float)
    for feature,expected in (
        ("weekday_sin",np.sin(2.0*math.pi*wd/7.0)),
        ("weekday_cos",np.cos(2.0*math.pi*wd/7.0)),
    ):
        got=resolve_feature(wc,{"family":"time","feature":feature,"parameters":{}},sec)
        assert _same(got,expected),feature
    v1_cases=[
        {"family":"momentum","feature":"RSI","parameters":{"window":5}},
        {"family":"trend","feature":"MACD","parameters":{"fast":5,"slow":13,"signal":5}},
        {"family":"volatility","feature":"TRUE_RANGE","parameters":{}},
        {"family":"price_action","feature":"body","parameters":{}},
        {"family":"volume","feature":"VWAP","parameters":{}},
        {"family":"crypto_microstructure","feature":"trades","parameters":{}},
    ]
    for cond in v1_cases:
        assert _same(resolve_feature(cache,cond,sec),v1.resolve_feature(cache,cond,sec)),cond["feature"]
    _expect_fail(lambda:resolve_feature(cache,{"family":"volatility","feature":"NATR","parameters":{}},sec),"MISSING_WINDOW")
    _expect_fail(lambda:resolve_feature(cache,{"family":"volatility","feature":"NATR","parameters":{"window":14.0}},sec),"FLOAT_WINDOW")
    _expect_fail(lambda:resolve_feature(cache,{"family":"volume","feature":"VWAP_DISTANCE","parameters":{"window":5}},sec),"EXTRA_PARAMETER")
    _expect_fail(lambda:resolve_feature(cache,{"family":"momentum","feature":"ULTIMATE_OSCILLATOR","parameters":{"parameter_set":[7,14,27]}},sec),"BAD_PARAMETER_SET")
    _expect_fail(lambda:resolve_feature(cache,{"family":"market_structure","feature":"breakout_high","parameters":{"window":5}},sec),"DEFERRED_FEATURE")
    missing=dict(cache)
    missing.pop("trades")
    _expect_fail(lambda:resolve_feature(missing,{"family":"crypto_microstructure","feature":"trades","parameters":{}},sec),"MICROSTRUCTURE_MISSING")
    print("V57_V433_FEATURE_RESOLVER_V2_SELF_CHECK=PASS|NEW_FEATURES=18|V1_DELEGATION=PASS|PARAM_FAIL_CLOSED=PASS|DEFERRED_FAIL_CLOSED=PASS|MICRO_FAIL_CLOSED=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
