from pathlib import Path
import hashlib,json,sys
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
V56=(Path("research_agent_v56_strategy_factory")/"src").resolve()
for p in (SRC,V56):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v56_fold_evaluator_v3 as v56

ENGINE="V57_V433_FOLD_SIGNAL_ADAPTER_V2"
MANIFEST_PATH=ROOT/"config/v433/V57_V433_FEATURE_CACHE_V2_MANIFEST_V2.json"
V56_PATH=V56/"v56_fold_evaluator_v3.py"
EXPECTED_MANIFEST_SHA="b2273621beb98e6204dec42c450b78c9f5047417b71347738462394330998b4b"
EXPECTED_V56_SHA="21ffe91528f0db7c3828ef1210d9b8466f706fdad80510cefb107cba716b41d4"
_MAN=None

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _ensure():
    global _MAN
    if _MAN is not None:
        return
    if _sha256(MANIFEST_PATH)!=EXPECTED_MANIFEST_SHA:
        raise RuntimeError("ADAPTER_V2_MANIFEST_ANCHOR_MISMATCH")
    if _sha256(V56_PATH)!=EXPECTED_V56_SHA:
        raise RuntimeError("ADAPTER_V2_V56_ANCHOR_MISMATCH")
    _MAN=json.loads(MANIFEST_PATH.read_text())
    if _MAN.get("contexts")!=24 or len(_MAN.get("entries",[]))!=24:
        raise RuntimeError("ADAPTER_V2_BAD_MANIFEST")
    if len(v56.POL["folds"])!=3:
        raise RuntimeError("ADAPTER_V2_BAD_FOLD_COUNT")

def load_v57_cache(market,timeframe):
    _ensure()
    q=[e for e in _MAN["entries"] if e["market"]==str(market) and e["timeframe"]==str(timeframe)]
    if len(q)!=1:
        raise ValueError("CACHE_V2_ENTRY_NOT_UNIQUE")
    e=q[0]
    p=Path(e["cache"])
    if not p.is_file():
        raise FileNotFoundError(p)
    if _sha256(p)!=e["cache_sha256"]:
        raise RuntimeError("CACHE_V2_HASH_MISMATCH:"+str(market)+":"+str(timeframe))
    with np.load(p,allow_pickle=False) as z:
        cache={k:z[k] for k in z.files}
    if "time" not in cache:
        raise KeyError("CACHE_KEY_MISSING:time")
    return p,cache

def prepare_context(market,timeframe):
    _ensure()
    ctx=v56.prepare_context(market,timeframe)
    p,cache=load_v57_cache(market,timeframe)
    tt=np.asarray(cache["time"],dtype=np.int64)
    vt=np.asarray(ctx["tf_time"],dtype=np.int64)
    if tt.shape!=vt.shape or not np.array_equal(tt,vt):
        raise ValueError("V57_V2_V56_TIME_ALIGNMENT_MISMATCH")
    ctx["v57_cache_path"]=str(p)
    ctx["v57_cache"]=cache
    ctx["v57_cache_version"]="V2"
    return ctx

def fold_masks(ctx,fold_index):
    _ensure()
    i=int(fold_index)
    if i<0 or i>=len(v56.POL["folds"]):
        raise ValueError("BAD_FOLD_INDEX:"+str(i))
    return v56.fold_masks(ctx,v56.POL["folds"][i])

def self_check():
    _ensure()
    markets=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
    timeframes=("M5","M15","M30","H1")
    contexts=0
    folds=0
    for market in markets:
        for timeframe in timeframes:
            ctx=prepare_context(market,timeframe)
            n=len(ctx["v57_cache"]["time"])
            contexts+=1
            for i in range(3):
                train,valid=fold_masks(ctx,i)
                train=np.asarray(train,dtype=bool)
                valid=np.asarray(valid,dtype=bool)
                if train.shape!=(n,) or valid.shape!=(n,):
                    raise AssertionError("BAD_FOLD_SHAPE")
                if not np.any(train) or not np.any(valid):
                    raise AssertionError("EMPTY_FOLD")
                if np.any(train&valid):
                    raise AssertionError("TRAIN_VALID_OVERLAP")
                folds+=1
    if contexts!=24 or folds!=72:
        raise AssertionError("BAD_COUNTS")
    print("V57_V433_FOLD_SIGNAL_ADAPTER_V2_SELF_CHECK=PASS|CONTEXTS=24|FOLDS=72|CACHE_V2=PASS|TIME_ALIGNMENT=PASS|TRAIN_VALID_ISOLATION=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
