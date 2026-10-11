import argparse
import copy
import fcntl
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parent
sys.path[:0]=[str(ROOT/"src/v433"),str(ROOT/"src")]

import v57_qd_cycle_runner_v1 as q
import v57_qd_archive_engine_v1 as archive

POLICY=ROOT/"config/v433/V57_V433_AUTOPILOT_POLICY_V1.json"
FREEZE=ROOT/"config/v433/V57_V433_AUTOPILOT_FREEZE_V1.json"
SEARCHER_FREEZE=ROOT/"config/v433/V57_V433_QD_SEARCHER_V433_FREEZE_V1.json"
BASELINE_JOURNAL=ROOT/"work/v433_qd_cycle_4096_execution_v1/V57_V433_QD_CYCLE_4096_RECORDS_V1.jsonl"
STATE=ROOT/"work/autopilot_v433"
CYCLES=STATE/"cycles"
STOP=STATE/"STOP"

BASE_SEED=943310
SEARCHER_SHA="63c576967dfc01c9fd1820074d19ff6713acda48947d11840c64af59af6924e8"
RUNNER_SHA="f80e8aa01a9292671bcbb5ae88a0d3766abcd0a0a2c4b7503c57ee61d7af420c"
BASELINE_JOURNAL_SHA="10278129b9c04b106df4803617dc4a0cbb1e89e7462646cb2adee241c5644edd"

_orig_ensure=q._ensure
_orig_bootstrap=q._bootstrap
_orig_explore=q.orchestrator.exploration_items
CURRENT_BASE_AR=None
CURRENT_BASE_SEEN=frozenset()

def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path,default=None):
    path=Path(path)
    return json.loads(path.read_text()) if path.exists() else default

def save(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+chr(10))
    os.replace(tmp,path)

def policy():
    x=load(POLICY)
    if not x or x.get("kind")!="V57_V433_AUTOPILOT_POLICY_V1" or x.get("status")!="FROZEN_BEFORE_AUTOPILOT_RUN":
        raise RuntimeError("AUTOPILOT_POLICY_INVALID")
    return x

def verify():
    if H(SEARCHER_FREEZE)!=SEARCHER_SHA:
        raise RuntimeError("SEARCHER_FREEZE_HASH_DRIFT")
    if H(ROOT/"src/v433/v57_qd_cycle_runner_v1.py")!=RUNNER_SHA:
        raise RuntimeError("QD_RUNNER_HASH_DRIFT")
    if H(BASELINE_JOURNAL)!=BASELINE_JOURNAL_SHA:
        raise RuntimeError("BASELINE_JOURNAL_HASH_DRIFT")
    p=policy()
    ri=p["research_integrity"]
    keys=("holdout_authorized","holdout_read","holdout_evaluated","september_2026_data_accessed","demo_orders_allowed","real_orders_allowed")
    if any(ri[k] is not False for k in keys):
        raise RuntimeError("RESEARCH_INTEGRITY_DRIFT")
    if FREEZE.exists():
        f=load(FREEZE)
        if H(__file__)!=f["runner"]["sha256"] or H(POLICY)!=f["policy"]["sha256"]:
            raise RuntimeError("AUTOPILOT_FREEZE_HASH_DRIFT")
    old=q.SEED
    q.SEED=BASE_SEED
    try:
        _orig_ensure()
    finally:
        q.SEED=old
    return True

def initial_base():
    ar,seen=_orig_bootstrap()
    rows,_=q._read_journal(BASELINE_JOURNAL)
    for r in rows:
        sid=r["strategy"]["strategy_id"]
        if sid in seen:
            raise RuntimeError("BASELINE_DUPLICATE:"+sid)
        q._apply(ar,r)
        seen.add(sid)
    archive.rebuild(ar)
    archive.validate(ar)
    if len(seen)!=4322:
        raise RuntimeError("BASELINE_SEEN_MISMATCH:"+str(len(seen)))
    if len(ar["exact_backlog"])!=24:
        raise RuntimeError("BASELINE_EXACT_BACKLOG_MISMATCH:"+str(len(ar["exact_backlog"])))
    return ar,seen

def state_obj(ar,seen,through_cycle):
    return {"schema_version":1,"kind":"V57_V433_AUTOPILOT_CUMULATIVE_STATE_V1","through_cycle":int(through_cycle),"archive":ar,"seen_strategy_ids":sorted(seen)}

def load_archive_state(path):
    x=load(path)
    if not x or x.get("kind")!="V57_V433_AUTOPILOT_CUMULATIVE_STATE_V1":
        raise RuntimeError("BAD_CUMULATIVE_STATE")
    ar=x["archive"]
    seen=set(x["seen_strategy_ids"])
    archive.rebuild(ar)
    archive.validate(ar)
    return ar,seen,int(x["through_cycle"])

def seed_for(cycle):
    p=policy()["cycle"]
    return int(p["seed_base"])+int(cycle)*int(p["seed_stride"])

def unseen_explore(count,seed,start,blocked):
    target=int(start)+int(count)
    got=[]
    used=set()
    cursor=0
    chunk=max(256,min(4096,target+256))
    while len(got)<target:
        batch=_orig_explore(chunk,int(seed),cursor)
        if not batch:
            raise RuntimeError("EXPLORATION_GENERATOR_EXHAUSTED")
        cursor+=len(batch)
        for item in batch:
            sid=item["strategy"]["strategy_id"]
            if sid in blocked or sid in used:
                continue
            used.add(sid)
            got.append(item)
            if len(got)>=target:
                break
        if cursor>10000000:
            raise RuntimeError("EXPLORATION_UNSEEN_SEARCH_LIMIT")
    return got[int(start):target]

def cycle_bootstrap():
    if CURRENT_BASE_AR is None:
        raise RuntimeError("AUTOPILOT_BASE_NOT_LOADED")
    return copy.deepcopy(CURRENT_BASE_AR),set(CURRENT_BASE_SEEN)

def cycle_explore(count,seed,start=0):
    return unseen_explore(count,seed,start,CURRENT_BASE_SEEN)

def cycle_ensure():
    old=q.SEED
    q.SEED=BASE_SEED
    try:
        _orig_ensure()
    finally:
        q.SEED=old
    return True

def base_for_cycle(cycle,cdir):
    bf=cdir/"base_state.json"
    if bf.exists():
        ar,seen,through=load_archive_state(bf)
        if through!=cycle-1:
            raise RuntimeError("CYCLE_BASE_VERSION_MISMATCH")
        return ar,seen
    cum=STATE/"cumulative_state.json"
    if cum.exists():
        ar,seen,through=load_archive_state(cum)
        if through!=cycle-1:
            raise RuntimeError("CUMULATIVE_VERSION_MISMATCH:"+str(through)+"/"+str(cycle-1))
    else:
        if cycle!=1:
            raise RuntimeError("MISSING_CUMULATIVE_STATE")
        ar,seen=initial_base()
        through=0
        save(cum,state_obj(ar,seen,through))
    save(bf,state_obj(ar,seen,through))
    return ar,seen

def cycle_once(st):
    global CURRENT_BASE_AR,CURRENT_BASE_SEEN
    verify()
    cycle=int(st.get("next_cycle",1))
    seed=seed_for(cycle)
    cdir=CYCLES/("cycle_%06d"%cycle)
    cdir.mkdir(parents=True,exist_ok=True)
    base_ar,base_seen=base_for_cycle(cycle,cdir)
    CURRENT_BASE_AR=base_ar
    CURRENT_BASE_SEEN=frozenset(base_seen)
    q.SEED=seed
    q._ensure=cycle_ensure
    q._bootstrap=cycle_bootstrap
    q.orchestrator.exploration_items=cycle_explore
    try:
        result=q.run(cdir)
        rows,_=q._read_journal(cdir/"V57_V433_QD_CYCLE_4096_RECORDS_V1.jsonl")
        ar,seen,phase=q._rebuild(rows)
        archive.rebuild(ar)
        archive.validate(ar)
    finally:
        q.SEED=BASE_SEED
        q._ensure=_orig_ensure
        q._bootstrap=_orig_bootstrap
        q.orchestrator.exploration_items=_orig_explore
        CURRENT_BASE_AR=None
        CURRENT_BASE_SEEN=frozenset()
    if result.get("status")!="COMPLETE":
        raise RuntimeError("AUTOPILOT_CYCLE_NOT_COMPLETE")
    save(STATE/"cumulative_state.json",state_obj(ar,seen,cycle))
    wrapper={"schema_version":1,"kind":"V57_V433_AUTOPILOT_CYCLE_V1","status":"CYCLE_COMPLETE","cycle":cycle,"seed":seed,"completed_candidates":result["completed_candidates"],"exact_pass_cycle":result["exact_pass"],"exact_backlog_total":len(ar["exact_backlog"]),"global_seen_total":len(seen),"search_result_sha256":H(cdir/"V57_V433_QD_CYCLE_4096_RESULT_V1.json"),"holdout_read":False,"holdout_evaluated":False,"demo_orders_allowed":False,"real_orders_allowed":False}
    save(cdir/"autopilot_cycle_result.json",wrapper)
    st["next_cycle"]=cycle+1
    st["last_cycle_completed"]=cycle
    st["last_seed"]=seed
    st["global_seen_total"]=len(seen)
    st["exact_backlog_total"]=len(ar["exact_backlog"])
    save(STATE/"state.json",st)
    print("AUTOPILOT_CYCLE_COMPLETE="+str(cycle)+"|SEED="+str(seed)+"|ATTEMPTS="+str(result["completed_candidates"])+"|GLOBAL_SEEN="+str(len(seen))+"|EXACT_BACKLOG="+str(len(ar["exact_backlog"])),flush=True)
    return wrapper

def self_check():
    verify()
    ar,seen=initial_base()
    s1=seed_for(1)
    items=unseen_explore(8,s1,0,seen)
    ids=[x["strategy"]["strategy_id"] for x in items]
    if len(ids)!=8 or len(set(ids))!=8 or any(x in seen for x in ids):
        raise RuntimeError("GLOBAL_DEDUP_SELF_CHECK_FAILED")
    if s1==BASE_SEED:
        raise RuntimeError("SEED_PROGRESSION_FAILED")
    print("V57_V433_AUTOPILOT_SELF_CHECK=PASS|MODES=ONE_SHOT,BATCH,CONTINUOUS|BASELINE_SEEN=4322|BASELINE_EXACT=24|NEXT_SEED="+str(s1)+"|GLOBAL_DEDUP=YES|ARCHIVE_CARRY_FORWARD=YES|HOLDOUT=UNREAD|ORDERS=DISABLED")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["ONE_SHOT","BATCH","CONTINUOUS"],default="ONE_SHOT")
    ap.add_argument("--cycles",type=int,default=1)
    ap.add_argument("--self-check",action="store_true")
    args=ap.parse_args()
    if args.self_check:
        self_check()
        return
    verify()
    if args.mode=="BATCH" and args.cycles<1:
        raise RuntimeError("BAD_BATCH_COUNT")
    STATE.mkdir(parents=True,exist_ok=True)
    CYCLES.mkdir(parents=True,exist_ok=True)
    lock=(STATE/"autopilot.lock").open("w")
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("AUTOPILOT_ALREADY_RUNNING")
    st=load(STATE/"state.json",{"schema_version":1,"kind":"V57_V433_AUTOPILOT_STATE_V1","next_cycle":1})
    done=0
    while True:
        if STOP.exists():
            print("AUTOPILOT_STOPPED_BY_STOP_FILE="+str(STOP))
            return
        free=shutil.disk_usage(REPO).free/1024**3
        minimum=float(policy()["runtime"]["minimum_free_gb"])
        if free<minimum:
            print("AUTOPILOT_PAUSED_LOW_DISK_GB="+str(round(free,2)),flush=True)
            time.sleep(int(policy()["runtime"]["low_disk_sleep_seconds"]))
            continue
        cycle_once(st)
        done+=1
        if args.mode=="ONE_SHOT":
            return
        if args.mode=="BATCH" and done>=args.cycles:
            return
        time.sleep(int(policy()["runtime"]["between_cycles_seconds"]))

if __name__=="__main__":
    main()
