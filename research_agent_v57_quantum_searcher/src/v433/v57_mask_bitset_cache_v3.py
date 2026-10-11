from pathlib import Path
import hashlib
import sys
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
ROOT=SRC.parent
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_candidate_signal_engine_v1 as legacy
import v57_mask_bitset_cache_v1 as cache_v1
import v57_feature_resolver_v2 as resolver2
import v57_transform_engine_v2 as transforms2

ENGINE="V57_V433_MASK_BITSET_CACHE_V3"

CANDIDATE_ENGINE_PATH=SRC/"v57_candidate_signal_engine_v1.py"
TRANSFORM_ENGINE_PATH=SRC/"v57_transform_engine_v1.py"
MASK_V1_PATH=V433/"v57_mask_bitset_cache_v1.py"
RESOLVER_V2_PATH=V433/"v57_feature_resolver_v2.py"
FEATURE_FREEZE_PATH=ROOT/"config/v433/V57_V433_FEATURE_CACHE_RESOLVER_FREEZE_V1.json"
MANIFEST_V2_PATH=ROOT/"config/v433/V57_V433_FEATURE_CACHE_V2_MANIFEST_V2.json"

EXPECTED_SHA256={
    str(CANDIDATE_ENGINE_PATH):"a60f074853e4c26f78d3d09d8c82c8c4e7e75297e212b9edd5b03f5ddbfc2e48",
    str(TRANSFORM_ENGINE_PATH):"19b06639b5ed09a6541deeec7fc63021f2102839954869796dc2d1a8c38b733f",
    str(MASK_V1_PATH):"975d787b5d22699355d0996c567adfac85ff28171c23ae90b8921aed82939617",
    str(RESOLVER_V2_PATH):"598391917542f5acda6a86408af64db4367e649336e5359f095fb781c64c2ee9",
    str(FEATURE_FREEZE_PATH):"96586473fd36baee26aa41248ef7ec8a6a38c41513b578d52854dbd13383ad70",
    str(MANIFEST_V2_PATH):"b2273621beb98e6204dec42c450b78c9f5047417b71347738462394330998b4b",
}
_VERIFIED=False

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _ensure_anchors():
    global _VERIFIED
    if _VERIFIED:
        return
    for p,h in EXPECTED_SHA256.items():
        got=_sha256(p)
        if got!=h:
            raise RuntimeError("V433_MASK_BITSET_CACHE_V2_ANCHOR_MISMATCH:"+p+":"+got)
    _VERIFIED=True

def condition_series_v2(cache,condition,sec,market=None):
    _ensure_anchors()
    if not isinstance(condition,dict):
        raise ValueError("CONDITION_NOT_DICT")
    base=resolver2.resolve_feature(cache,condition,int(sec),market)
    kind=str(condition["transform"])
    if kind in legacy.EVENT_TRANSFORMS:
        return np.asarray(base,dtype=float)
    if kind not in legacy.NUMERIC_TRANSFORMS:
        raise ValueError("UNKNOWN_TRANSFORM:"+kind)
    n=None if kind=="LEVEL" else condition.get("lookback")
    if kind!="LEVEL" and n is None:
        raise ValueError("LOOKBACK_REQUIRED:"+kind)
    return transforms2.transform(
        np.asarray(base,dtype=float),
        np.asarray(cache["time"],dtype=np.int64),
        int(sec),
        kind,
        None if n is None else int(n),
    )

class MaskBitsetCache:
    def __init__(self):
        _ensure_anchors()
        self._series={}
        self._masks={}
        self._stats={"series_hits":0,"series_misses":0,"mask_hits":0,"mask_misses":0}

    def clear(self):
        self._series.clear()
        self._masks.clear()
        for k in self._stats:
            self._stats[k]=0

    def stats(self):
        packed_bytes=int(sum(v["packed"].nbytes for v in self._masks.values()))
        series_bytes=int(sum(v.nbytes for v in self._series.values()))
        return dict(
            self._stats,
            series_entries=len(self._series),
            mask_entries=len(self._masks),
            packed_mask_bytes=packed_bytes,
            series_bytes=series_bytes,
        )

    def condition_mask(self,cache,condition,sec,train_mask,market=None,context_id=None):
        _ensure_anchors()
        if "time" not in cache:
            raise KeyError("CACHE_KEY_MISSING:time")
        n=len(np.asarray(cache["time"]))
        tm=np.asarray(train_mask,dtype=bool)
        if tm.shape!=(n,):
            raise ValueError("BAD_TRAIN_MASK_SHAPE")
        ctx=cache_v1.context_key(cache,sec,market,context_id)
        ckey=cache_v1.condition_key(condition)
        tkey=cache_v1.train_key(tm)
        mkey=(ctx,tkey,ckey)
        hit=self._masks.get(mkey)
        if hit is not None:
            self._stats["mask_hits"]+=1
            return cache_v1.unpack_mask(hit["packed"],hit["n"]),float(hit["threshold"])

        self._stats["mask_misses"]+=1
        skey=(ctx,cache_v1.series_condition_key(condition))
        series=self._series.get(skey)
        if series is None:
            self._stats["series_misses"]+=1
            series=np.asarray(condition_series_v2(cache,condition,int(sec),market),dtype=float)
            if series.shape!=(n,):
                raise ValueError("BAD_CONDITION_SERIES_SHAPE")
            self._series[skey]=series
        else:
            self._stats["series_hits"]+=1

        finite_train=np.isfinite(series) & tm
        if not np.any(finite_train):
            raise ValueError("NO_FINITE_TRAIN_VALUES")
        quantile=float(condition["threshold_quantile"])
        threshold=float(legacy.fit_threshold(series,tm,quantile))
        kind=str(condition["transform"])
        if kind in legacy.EVENT_TRANSFORMS:
            mask=legacy.event_threshold_mask(series,cache["time"],int(sec),threshold,kind)
        elif kind in legacy.NUMERIC_TRANSFORMS:
            mask=legacy.numeric_threshold_mask(series,threshold,quantile)
        else:
            raise ValueError("UNKNOWN_TRANSFORM:"+kind)
        mask=np.asarray(mask,dtype=bool)
        if mask.shape!=(n,):
            raise ValueError("BAD_CONDITION_MASK_SHAPE")
        packed,count=cache_v1.pack_mask(mask)
        self._masks[mkey]={"packed":packed,"n":count,"threshold":threshold}
        return mask.copy(),threshold

def _same_float(a,b):
    a=np.asarray(a,dtype=float)
    b=np.asarray(b,dtype=float)
    return a.shape==b.shape and np.array_equal(a,b,equal_nan=True)

def _oracle(cache,condition,sec,train_mask,market=None):
    series=condition_series_v2(cache,condition,sec,market)
    q=float(condition["threshold_quantile"])
    th=float(legacy.fit_threshold(series,train_mask,q))
    kind=str(condition["transform"])
    if kind in legacy.EVENT_TRANSFORMS:
        mask=legacy.event_threshold_mask(series,cache["time"],int(sec),th,kind)
    else:
        mask=legacy.numeric_threshold_mask(series,th,q)
    return np.asarray(mask,dtype=bool),th,np.asarray(series,dtype=float)

def self_check():
    _ensure_anchors()
    n=10
    t=np.arange(n,dtype=np.int64)*86400
    cache={
        "time":t,
        "open":np.linspace(100.0,109.0,n),
        "high":np.linspace(101.0,111.0,n),
        "low":np.linspace(99.0,108.0,n),
        "close":np.array([100.,101.,103.,102.,105.,107.,106.,109.,108.,111.]),
        "volume":np.linspace(10.0,19.0,n),
    }
    cond={"family":"time","feature":"weekday_sin","parameters":{},"transform":"LEVEL","threshold_quantile":0.5}
    train_a=np.array([1,1,1,1,1,0,0,0,0,0],dtype=bool)
    train_b=~train_a
    c=MaskBitsetCache()
    oa,tha,sa=_oracle(cache,cond,86400,train_a,"TEST")
    ma,cha=c.condition_mask(cache,cond,86400,train_a,"TEST","TEST|D1")
    if not np.array_equal(ma,oa) or cha!=tha:
        raise AssertionError("ORACLE_PARITY_A")
    ma2,cha2=c.condition_mask(cache,cond,86400,train_a,"TEST","TEST|D1")
    if not np.array_equal(ma2,ma) or cha2!=cha:
        raise AssertionError("WARM_MASK_HIT")
    ob,thb,sb=_oracle(cache,cond,86400,train_b,"TEST")
    mb,chb=c.condition_mask(cache,cond,86400,train_b,"TEST","TEST|D1")
    if not np.array_equal(mb,ob) or chb!=thb:
        raise AssertionError("ORACLE_PARITY_B")
    if not _same_float(sa,sb):
        raise AssertionError("SERIES_NOT_SHARED")
    if tha==thb:
        raise AssertionError("TRAIN_ISOLATION_THRESHOLD_NOT_DISTINCT")

    event=dict(cond)
    event["transform"]="CROSS_UP"
    oe,the,_=_oracle(cache,event,86400,train_a,"TEST")
    me,che=c.condition_mask(cache,event,86400,train_a,"TEST","TEST|D1")
    if not np.array_equal(me,oe) or che!=the:
        raise AssertionError("EVENT_PARITY")

    packed,count=cache_v1.pack_mask(ma)
    if count!=n or not np.array_equal(cache_v1.unpack_mask(packed,count),ma):
        raise AssertionError("PACKBITS_ROUNDTRIP")
    st=c.stats()
    if st["mask_hits"]<1 or st["mask_misses"]<3 or st["series_hits"]<1:
        raise AssertionError("CACHE_STATS:"+str(st))
    print("V57_V433_MASK_BITSET_CACHE_V2_SELF_CHECK=PASS|RESOLVER_V2=PASS|LEGACY_TRANSFORMS=PASS|TRAIN_ISOLATION=PASS|EVENT_SEGMENTS=PASS|PACKBITS=PASS|WARM_HIT=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
