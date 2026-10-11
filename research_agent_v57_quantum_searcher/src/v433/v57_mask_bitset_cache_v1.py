from pathlib import Path
import hashlib
import json
import sys
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_candidate_signal_engine_v1 as legacy
import v57_strategy_dsl_v3 as dsl3

ENGINE="V57_V433_MASK_BITSET_CACHE_V1"

def _sha_bytes(*parts):
    h=hashlib.sha256()
    for part in parts:
        if isinstance(part,str):
            part=part.encode("utf-8")
        h.update(len(part).to_bytes(8,"big"))
        h.update(part)
    return h.hexdigest()

def _canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")

def condition_key(condition):
    if not isinstance(condition,dict):
        raise ValueError("CONDITION_NOT_DICT")
    return hashlib.sha256(_canonical(condition)).hexdigest()

def series_condition_key(condition):
    if not isinstance(condition,dict):
        raise ValueError("CONDITION_NOT_DICT")
    x=dict(condition)
    x.pop("threshold_quantile",None)
    return hashlib.sha256(_canonical(x)).hexdigest()

def train_key(train_mask):
    m=np.asarray(train_mask,dtype=bool)
    if m.ndim!=1:
        raise ValueError("BAD_TRAIN_MASK_DIM")
    packed=np.packbits(m,bitorder="little")
    return _sha_bytes(str(len(m)),packed.tobytes())

def context_key(cache,sec,market,context_id=None):
    if "time" not in cache:
        raise KeyError("CACHE_KEY_MISSING:time")
    t=np.asarray(cache["time"],dtype=np.int64)
    if t.ndim!=1:
        raise ValueError("BAD_TIME_DIM")
    cid="" if context_id is None else str(context_id)
    return _sha_bytes(str(market),str(int(sec)),cid,str(len(t)),t.tobytes())

def pack_mask(mask):
    m=np.asarray(mask,dtype=bool)
    if m.ndim!=1:
        raise ValueError("BAD_MASK_DIM")
    return np.packbits(m,bitorder="little"),int(len(m))

def unpack_mask(packed,n):
    p=np.asarray(packed,dtype=np.uint8)
    return np.unpackbits(p,bitorder="little",count=int(n)).astype(bool,copy=False)

class MaskBitsetCache:
    def __init__(self):
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
        return dict(self._stats,series_entries=len(self._series),mask_entries=len(self._masks),packed_mask_bytes=packed_bytes,series_bytes=series_bytes)

    def condition_mask(self,cache,condition,sec,train_mask,market=None,context_id=None):
        if "time" not in cache:
            raise KeyError("CACHE_KEY_MISSING:time")
        n=len(np.asarray(cache["time"]))
        tm=np.asarray(train_mask,dtype=bool)
        if tm.shape!=(n,):
            raise ValueError("BAD_TRAIN_MASK_SHAPE")
        ctx=context_key(cache,sec,market,context_id)
        ckey=condition_key(condition)
        tkey=train_key(tm)
        mkey=(ctx,tkey,ckey)
        hit=self._masks.get(mkey)
        if hit is not None:
            self._stats["mask_hits"]+=1
            return unpack_mask(hit["packed"],hit["n"]),float(hit["threshold"])

        self._stats["mask_misses"]+=1
        skey=(ctx,series_condition_key(condition))
        series=self._series.get(skey)
        if series is None:
            self._stats["series_misses"]+=1
            series=np.asarray(legacy.condition_series(cache,condition,int(sec),market),dtype=float)
            if series.shape!=(n,):
                raise ValueError("BAD_CONDITION_SERIES_SHAPE")
            self._series[skey]=series
        else:
            self._stats["series_hits"]+=1

        q=float(condition["threshold_quantile"])
        threshold=float(legacy.fit_threshold(series,tm,q))
        kind=str(condition["transform"])
        if kind in legacy.EVENT_TRANSFORMS:
            mask=legacy.event_threshold_mask(series,cache["time"],int(sec),threshold,kind)
        elif kind in legacy.NUMERIC_TRANSFORMS:
            mask=legacy.numeric_threshold_mask(series,threshold,q)
        else:
            raise ValueError("UNKNOWN_TRANSFORM:"+kind)
        mask=np.asarray(mask,dtype=bool)
        if mask.shape!=(n,):
            raise ValueError("BAD_CONDITION_MASK_SHAPE")
        packed,count=pack_mask(mask)
        self._masks[mkey]={"packed":packed,"n":count,"threshold":threshold}
        return mask.copy(),threshold

def self_check():
    n=8
    cache={"time":np.arange(n,dtype=np.int64)*60,"X":np.arange(n,dtype=float)}
    condition={"family":"test","feature":"X","transform":"LEVEL","threshold_quantile":0.5}
    original=legacy.resolver.resolve_feature
    legacy.resolver.resolve_feature=lambda cache,condition,sec,market=None: np.asarray(cache[condition["feature"]],dtype=float)
    try:
        c=MaskBitsetCache()
        train_a=np.array([1,1,1,1,0,0,0,0],dtype=bool)
        train_b=np.array([0,0,0,0,1,1,1,1],dtype=bool)

        legacy_a,legacy_th_a,_=legacy.condition_mask(cache,condition,60,train_a,"TEST")
        mask_a,th_a=c.condition_mask(cache,condition,60,train_a,"TEST","TEST_M1")
        if not np.array_equal(mask_a,legacy_a) or th_a!=float(legacy_th_a):
            raise AssertionError("LEGACY_PARITY_A")

        mask_a2,th_a2=c.condition_mask(cache,condition,60,train_a,"TEST","TEST_M1")
        if not np.array_equal(mask_a2,mask_a) or th_a2!=th_a:
            raise AssertionError("MASK_CACHE_HIT_MISMATCH")

        legacy_b,legacy_th_b,_=legacy.condition_mask(cache,condition,60,train_b,"TEST")
        mask_b,th_b=c.condition_mask(cache,condition,60,train_b,"TEST","TEST_M1")
        if not np.array_equal(mask_b,legacy_b) or th_b!=float(legacy_th_b):
            raise AssertionError("LEGACY_PARITY_B")
        if th_a==th_b:
            raise AssertionError("TRAIN_ISOLATION_THRESHOLD_NOT_DISTINCT")

        packed,count=pack_mask(mask_a)
        if count!=n or not np.array_equal(unpack_mask(packed,count),mask_a):
            raise AssertionError("PACKBITS_ROUNDTRIP")

        st=c.stats()
        if st["series_misses"]!=1 or st["mask_misses"]!=2 or st["mask_hits"]!=1:
            raise AssertionError("CACHE_STATS:"+str(st))
    finally:
        legacy.resolver.resolve_feature=original
    print("V57_V433_MASK_BITSET_CACHE_V1_SELF_CHECK=PASS|LEGACY_PARITY=PASS|TRAIN_ISOLATION=PASS|PACKBITS=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
