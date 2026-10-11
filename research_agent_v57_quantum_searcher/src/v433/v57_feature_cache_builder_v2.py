from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

import v57_feature_cache_builder_v1 as v1

CONTRACT_PATH=ROOT/"config/v433/V57_V433_TIME_AND_CACHE_SEMANTICS_CONTRACT_V1.json"
SEMANTICS_PATH=ROOT/"config/V57_FEATURE_SEMANTICS_V1.json"
V1_BUILDER_PATH=SRC/"v57_feature_cache_builder_v1.py"
OUT=ROOT/"work/feature_cache_v2"
MARKETS=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
TFS={"M5":300,"M15":900,"M30":1800,"H1":3600}

EXPECTED_SHA256={
    str(CONTRACT_PATH):"63aadc48fe52aeb050bed009c14032581e4991859268d11179deddce6e0f21d7",
    str(SEMANTICS_PATH):"95a1940dd1205c685e6bfd9b9c529bd08f319914b9c61c11302c688a83647d70",
    str(V1_BUILDER_PATH):"affb4bb4cdef69e110cc5e64c02286edfcc4ec4d3093d0698888a36692491c60",
}
_VERIFIED=False

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def ensure_anchors():
    global _VERIFIED
    if _VERIFIED:
        return
    for p,h in EXPECTED_SHA256.items():
        got=digest(p)
        if got!=h:
            raise RuntimeError("V433_CACHE_BUILDER_V2_ANCHOR_MISMATCH:"+p+":"+got)
    _VERIFIED=True

def raw_indicator_time(t,sec,market):
    t=np.asarray(t,dtype=np.int64)
    return t.copy()

def build(market,tf):
    ensure_anchors()
    market=str(market); tf=str(tf)
    if market not in MARKETS:
        raise ValueError("BAD_MARKET:"+market)
    if tf not in TFS:
        raise ValueError("BAD_TIMEFRAME:"+tf)
    od=OUT/market
    final=od/(market+"_"+tf+"_V57_FEATURE_CACHE_V2.npz")
    final_meta=Path(str(final)+".json")
    if final.exists() or final_meta.exists():
        raise FileExistsError("V57_FEATURE_CACHE_V2_ALREADY_EXISTS:"+str(final))
    od.mkdir(parents=True,exist_ok=True)
    legacy=od/(market+"_"+tf+"_V57_FEATURE_CACHE_V1.npz")
    legacy_meta=Path(str(legacy)+".json")
    if legacy.exists() or legacy_meta.exists():
        raise FileExistsError("TEMP_LEGACY_NAME_COLLISION:"+str(legacy))
    old_out=v1.OUT
    old_time=v1.indicator_time
    try:
        v1.OUT=OUT
        v1.indicator_time=raw_indicator_time
        v1.build(market,tf)
    finally:
        v1.OUT=old_out
        v1.indicator_time=old_time
    if not legacy.is_file() or not legacy_meta.is_file():
        raise RuntimeError("V1_DELEGATED_BUILD_OUTPUT_MISSING")
    meta=json.loads(legacy_meta.read_text())
    source=Path(meta["source"])
    if not source.is_file() or digest(source)!=meta["source_sha256"]:
        raise RuntimeError("SOURCE_HASH_MISMATCH_AFTER_BUILD")
    legacy.rename(final)
    cache_hash=digest(final)
    if cache_hash!=meta["cache_sha256"]:
        raise RuntimeError("CACHE_HASH_CHANGED_ON_RENAME")
    meta.update({
        "schema_version":2,
        "kind":"V57_FEATURE_CACHE_V2",
        "cache":str(final),
        "cache_sha256":cache_hash,
        "time_semantics":{
            "bar_timestamp":"OPEN_TIME",
            "indicator_time_source":"RAW_SOURCE_TIME_ONLY",
            "synthetic_gap_compression":False,
            "rolling_state_resets_after_gap":True,
        },
        "builder_v2":{
            "path":str(Path(__file__)),
            "sha256":digest(Path(__file__)),
            "delegated_feature_generator":str(V1_BUILDER_PATH),
            "delegated_feature_generator_sha256":digest(V1_BUILDER_PATH),
            "indicator_time_override":"IDENTITY_RAW_TIME",
            "contract":str(CONTRACT_PATH),
            "contract_sha256":digest(CONTRACT_PATH),
            "feature_semantics_sha256":digest(SEMANTICS_PATH),
        },
        "research_integrity":{
            "holdout_read":False,
            "september_2026_data_accessed":False,
            "real_orders_allowed":False,
        },
    })
    final_meta.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    legacy_meta.unlink()
    with np.load(final,allow_pickle=False) as z:
        if not np.array_equal(np.asarray(z["time"],dtype=np.int64),raw_indicator_time(z["time"],TFS[tf],market)):
            raise AssertionError("RAW_TIME_IDENTITY_FAILED")
    print("V57_V433_FEATURE_CACHE_V2_BUILD=PASS|MARKET="+market+"|TF="+tf+"|ROWS="+str(meta["rows"])+"|FEATURES="+str(meta["features"])+"|RAW_TIME=PASS|ORDERS=DISABLED")
    print("CACHE_V2_SHA256="+cache_hash)

def self_check():
    ensure_anchors()
    t=np.array([0,300,600,1800,2100],dtype=np.int64)
    assert np.array_equal(raw_indicator_time(t,300,"XAUUSD"),t)
    assert np.array_equal(raw_indicator_time(t,300,"BTCUSD"),t)
    assert TFS=={"M5":300,"M15":900,"M30":1800,"H1":3600}
    assert len(MARKETS)==6
    print("V57_V433_FEATURE_CACHE_BUILDER_V2_SELF_CHECK=PASS|RAW_TIME_ONLY=PASS|V1_FEATURE_GENERATOR_HASHED=PASS|NO_V1_OVERWRITE=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--market")
    ap.add_argument("--tf")
    ap.add_argument("--self-check",action="store_true")
    args=ap.parse_args()
    if args.self_check:
        self_check()
    else:
        if args.market is None or args.tf is None:
            raise SystemExit("MARKET_AND_TF_REQUIRED")
        build(args.market,args.tf)
