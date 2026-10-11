import copy,hashlib,json,math,os,sys
from pathlib import Path
import v57_qd_archive_engine_v1 as archive
import v57_qd_orchestrator_engine_v1 as orchestrator
import v57_qd_scheduler_engine_v1 as scheduler
import v57_qd_checkpoint_resume_engine_v1 as checkpoint
import v57_qd_bootstrap_runner_v1 as boot

ENGINE="V57_V433_QD_CYCLE_RUNNER_V1"
HERE=Path(__file__).resolve()
ROOT=HERE.parents[2]
POLICY=ROOT/"config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
BOOT_FREEZE=ROOT/"config/v433/V57_V433_QD_BOOTSTRAP_2048_EXECUTION_FREEZE_V1.json"
BOOT_DIR=ROOT/"work/v433_qd_bootstrap_2048_execution_v1"
BOOT_CP=BOOT_DIR/"checkpoint_v1.json"
EXPLORE=1434
EXPLOIT=2662
TOTAL=4096
BATCH=128
SEED=943310
EXPECTED_BOOT_FREEZE_SHA="b32567e8c6a3ab0f5a2ac0f29a7feba88d4b26a208c969647382e8a1302dcf9b"

def H(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)

def _ensure():
    if H(BOOT_FREEZE)!=EXPECTED_BOOT_FREEZE_SHA:
        raise ValueError("BOOTSTRAP_FREEZE_HASH_DRIFT")
    f=json.loads(BOOT_FREEZE.read_text())
    if f.get("status")!="FROZEN_AFTER_BOOTSTRAP_2048_EXECUTION" or f.get("completed_candidates")!=2048:
        raise ValueError("BAD_BOOTSTRAP_FREEZE")
    runner=ROOT/f["runner"]["path"]
    if H(runner)!=f["runner"]["sha256"]:
        raise ValueError("BOOTSTRAP_RUNNER_HASH_DRIFT")
    p=json.loads(POLICY.read_text())
    c=p["budget"]["cycle"]
    if (c["exploration_budget"],c["exploitation_budget"],c["total_budget"],c["batch_size"],c["seed_base"])!=(EXPLORE,EXPLOIT,TOTAL,BATCH,SEED):
        raise ValueError("CYCLE_POLICY_DRIFT")
    if any(p["research_integrity"][k] is not False for k in ("holdout_authorized","holdout_read","holdout_evaluated","september_2026_data_accessed","demo_orders_allowed","real_orders_allowed")):
        raise ValueError("RESEARCH_INTEGRITY_DRIFT")
    archive._ensure(); orchestrator._ensure(); scheduler._ensure(); checkpoint._ensure(); boot._ensure()
    return True

def _read_journal(path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists(): return [],b""
    data=p.read_bytes()
    if data and not data.endswith(b"\n"):
        cut=data.rfind(b"\n")+1
        with p.open("r+b") as f:
            f.truncate(cut); f.flush(); os.fsync(f.fileno())
        data=data[:cut]
    rows=[]
    for i,line in enumerate(data.splitlines()):
        raw=json.loads(line)
        r=boot._json_unpack(raw) if hasattr(boot,"_json_unpack") else raw
        if r.get("candidate_index")!=i: raise ValueError("CYCLE_INDEX_MISMATCH:%d"%i)
        if r.get("status") not in ("EVALUATED","PREFILTER_REJECT"): raise ValueError("BAD_STATUS:%d"%i)
        if r.get("error") is not None: raise ValueError("ERROR_RECORD:%d"%i)
        ri=r.get("research_integrity",{})
        for k in ("holdout_read","holdout_evaluated","september_2026_data_accessed","demo_orders_allowed","real_orders_allowed"):
            if ri.get(k) is not False: raise ValueError("RI_VIOLATION:%d:%s"%(i,k))
        rows.append(r)
    if len(rows)>TOTAL: raise ValueError("CYCLE_OVER_BUDGET")
    return rows,data

def _append(path,r):
    p=Path(path); existed=p.exists()
    line=boot._record_line(r)
    with p.open("ab") as f:
        f.write(line); f.flush(); os.fsync(f.fileno())
    if not existed:
        try:
            fd=os.open(str(p.parent),os.O_DIRECTORY); os.fsync(fd); os.close(fd)
        except (AttributeError,OSError): pass
    return line

def _record_rankable(r):
    if r.get("status") != "EVALUATED":
        return False
    result = r.get("result")
    folds = result.get("folds") if isinstance(result, dict) else None
    if not isinstance(folds, list) or len(folds) != 3:
        raise ValueError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
    required = ("base_avg_bps", "stress_avg_bps", "base_pf", "stress_pf", "tpd", "selected_trades", "drawdown_bps")
    def bad(v):
        try:
            x = float(v)
        except (TypeError, ValueError):
            return True
        return x != x or x == float("inf") or x == float("-inf")
    return not any(bad(f.get(k)) for f in folds for k in required)

def _apply(ar,r):
    if r.get("status") == "EVALUATED" and not _record_rankable(r):
        result = r.get("result")
        if isinstance(result, dict) and bool(result.get("exact_pass")):
            raise ValueError("EXACT_PASS_UNRANKABLE_FORBIDDEN")
        ar["stats"]["input_records"] += 1
        ar["stats"]["evaluated_records"] += 1
        return 0
    return boot._apply_record_fast(ar,r)

def _match(r,item,i,phase,round_index):
    if r.get("candidate_index")!=i or r.get("phase")!=phase: raise ValueError("RECORD_PHASE_INDEX_DRIFT:%d"%i)
    if int(r.get("cycle_round",-1))!=int(round_index): raise ValueError("ROUND_DRIFT:%d"%i)
    if r.get("strategy",{}).get("strategy_id")!=item["strategy"]["strategy_id"]: raise ValueError("SID_DRIFT:%d"%i)
    if canonical(r.get("strategy"))!=canonical(item["strategy"]): raise ValueError("STRATEGY_DRIFT:%d"%i)
    if canonical(r.get("meta"))!=canonical(item["meta"]): raise ValueError("META_DRIFT:%d"%i)

def _bootstrap():
    s=checkpoint.load_checkpoint(BOOT_CP)
    if s["progress"]["phase"]!="COMPLETE" or int(s["progress"]["completed_candidates"])!=2048:
        raise ValueError("BOOTSTRAP_CHECKPOINT_NOT_COMPLETE")
    archive.validate(s["archive"])
    return copy.deepcopy(s["archive"]),set(s["seen_strategy_ids"])

def _rebuild(rows):
    ar,seen=_bootstrap()
    n=len(rows); expn=min(n,EXPLORE)
    if expn:
        items=orchestrator.exploration_items(expn,SEED,0)
        for i in range(expn):
            _match(rows[i],items[i],i,"CYCLE_EXPLORATION",-1)
            sid=items[i]["strategy"]["strategy_id"]
            if sid in seen: raise ValueError("DUPLICATE_EXPLORE:"+sid)
            _apply(ar,rows[i]); seen.add(sid)
    if n<EXPLORE:
        return ar,seen,{"phase":"CYCLE_EXPLORATION","round":-1,"parent_ids":[],"round_items":[],"round_done":0}
    archive.rebuild(ar); archive.validate(ar)
    parent_ids=scheduler.initial_parent_ids(ar,EXPLOIT)
    if not parent_ids: raise ValueError("NO_ELIGIBLE_PARENTS_AFTER_EXPLORATION")
    pos=EXPLORE; rnd=0; done=0
    while pos<n:
        remaining=EXPLOIT-done
        items=orchestrator.exploitation_items(ar,parent_ids,rnd,remaining,SEED,seen)
        if not items: raise ValueError("EMPTY_EXPLOITATION_ROUND:%d"%rnd)
        take=min(len(items),n-pos)
        rr=[]
        for j in range(take):
            i=pos+j; _match(rows[i],items[j],i,"CYCLE_EXPLOITATION",rnd)
            sid=items[j]["strategy"]["strategy_id"]
            if sid in seen: raise ValueError("DUPLICATE_EXPLOIT:"+sid)
            _apply(ar,rows[i]); seen.add(sid); rr.append(rows[i])
        pos+=take; done+=take
        if take<len(items):
            return ar,seen,{"phase":"CYCLE_EXPLOITATION","round":rnd,"parent_ids":parent_ids,"round_items":items,"round_done":take,"exploitation_done":done}
        if done>=EXPLOIT: break
        archive.rebuild(ar); archive.validate(ar)
        raw_survivors=scheduler.survivor_parent_ids(parent_ids,[x for x in rr if x.get("status") != "EVALUATED" or _record_rankable(x)])
        active_ids={e["strategy_id"] for e in archive.active_entries(ar)}
        parent_ids=[pid for pid in raw_survivors if pid in active_ids]
        if not parent_ids:
            return ar,seen,{"phase":"COMPLETE","round":rnd+1,"parent_ids":[],"round_items":[],"round_done":0,"exploitation_done":done,"exhausted":True}
        rnd+=1
    return ar,seen,{"phase":"COMPLETE" if n==TOTAL else "CYCLE_EXPLOITATION","round":rnd,"parent_ids":parent_ids,"round_items":[],"round_done":0,"exploitation_done":done}

def _checkpoint(out,ar,seen,rows,data,st):
    obj={"schema_version":1,"kind":"V57_V433_QD_CYCLE_CHECKPOINT_V1","engine":ENGINE,"completed_candidates":len(rows),"exploration_completed":min(len(rows),EXPLORE),"exploitation_completed":max(0,len(rows)-EXPLORE),"phase":st["phase"],"round":st.get("round",-1),"parent_ids":list(st.get("parent_ids",[])),"seen_strategy_ids":len(seen),"journal_records":len(rows),"journal_sha256":hashlib.sha256(data).hexdigest(),"archive":ar,"research_integrity":{"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"demo_orders_allowed":False,"real_orders_allowed":False}}
    raw=(json.dumps(boot._json_pack(obj) if hasattr(boot,"_json_pack") else obj,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    p=Path(out)/"checkpoint_cycle_v1.json"; t=p.with_suffix(".json.tmp")
    with t.open("wb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)
    try:
        fd=os.open(str(p.parent),os.O_DIRECTORY); os.fsync(fd); os.close(fd)
    except (AttributeError,OSError): pass
    return p

def _summary(out,ar,seen,rows,data,st):
    status={}
    exact=0
    for r in rows:
        status[r["status"]]=status.get(r["status"],0)+1
        if r["status"]=="EVALUATED" and isinstance(r.get("result"),dict) and bool(r["result"].get("exact_pass")): exact+=1
    ids=[r["strategy"]["strategy_id"] for r in rows]
    return {"schema_version":1,"kind":"V57_V433_QD_CYCLE_4096_RESULT_V1","status":"COMPLETE" if (len(rows)==TOTAL or bool(st.get("exhausted"))) else "PARTIAL","engine":ENGINE,"completed_candidates":len(rows),"budget":TOTAL,"exploration_budget":EXPLORE,"exploitation_budget":EXPLOIT,"exploitation_completed":max(0,len(rows)-EXPLORE),"exploitation_unused_budget":max(0,EXPLOIT-max(0,len(rows)-EXPLORE)),"exploitation_exhausted":bool(st.get("exhausted")),"seed_base":SEED,"status_counts":dict(sorted(status.items())),"evaluated":status.get("EVALUATED",0),"prefilter_reject":status.get("PREFILTER_REJECT",0),"exact_pass":exact,"archive_candidate_pool":len(ar["candidate_pool"]),"archive_active":len(archive.active_entries(ar)),"archive_exact_backlog":len(ar["exact_backlog"]),"all_candidate_ids_seen_cycle":len(rows),"all_candidate_ids_seen_total":len(seen),"candidate_sequence_sha256":hashlib.sha256("".join(ids).encode()).hexdigest(),"journal_sha256":hashlib.sha256(data).hexdigest(),"bootstrap_freeze_sha256":H(BOOT_FREEZE),"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"demo_orders_allowed":False,"real_orders_allowed":False,"shadow_authorized":False,"whitelist_created":False}

def run(outdir,stop_after=None):
    _ensure(); out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    jp=out/"V57_V433_QD_CYCLE_4096_RECORDS_V1.jsonl"; rp=out/"V57_V433_QD_CYCLE_4096_RESULT_V1.json"
    rows,data=_read_journal(jp); ar,seen,st=_rebuild(rows); completed=len(rows)
    target=TOTAL if stop_after is None else int(stop_after)
    if stop_after is None and bool(st.get("exhausted")): target=completed
    if target<completed or target>TOTAL: raise ValueError("BAD_STOP_AFTER")
    hasher=hashlib.sha256(); hasher.update(data); contexts,stores={},{}
    while completed<target:
        if completed<EXPLORE:
            n=min(BATCH,EXPLORE-completed,target-completed)
            items=orchestrator.exploration_items(n,SEED,completed)
            phase="CYCLE_EXPLORATION"; rnd=-1; start=0
        else:
            if st["phase"]!="CYCLE_EXPLOITATION":
                ar,seen,st=_rebuild(rows)
            rnd=st["round"]; phase="CYCLE_EXPLOITATION"
            if st.get("round_items"):
                items=st["round_items"]; start=st["round_done"]
            else:
                remaining=EXPLOIT-(completed-EXPLORE)
                items=orchestrator.exploitation_items(ar,st["parent_ids"],rnd,remaining,SEED,seen); start=0
                if not items:
                  st={"phase":"COMPLETE","round":rnd,"parent_ids":[],"round_items":[],"round_done":0,"exploitation_done":completed-EXPLORE,"exhausted":True}
                  data=jp.read_bytes() if jp.exists() else b""
                  archive.rebuild(ar); archive.validate(ar)
                  _checkpoint(out,ar,seen,rows,data,st)
                  result=_summary(out,ar,seen,rows,data,st)
                  rp.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
                  return result
            items=items[start:]
            if target-completed<len(items): items=items[:target-completed]
        round_records=[]
        for item in items:
            idx=completed; sid=item["strategy"]["strategy_id"]
            if sid in seen: raise ValueError("GLOBAL_DUPLICATE:"+sid)
            r=orchestrator.evaluate_item(item,phase,idx,contexts,stores)
            if r.get("status")=="ERROR": raise RuntimeError("CYCLE_EVALUATION_ERROR:%d:%s"%(idx,r.get("error")))
            if r.get("status") not in ("EVALUATED","PREFILTER_REJECT"): raise RuntimeError("CYCLE_BAD_STATUS:%d"%idx)
            r["cycle_round"]=rnd
            line=_append(jp,r); hasher.update(line); rows.append(r); _apply(ar,r); seen.add(sid); completed+=1; round_records.append(r)
            if completed%BATCH==0 or completed==target or completed==TOTAL:
                archive.rebuild(ar); archive.validate(ar)
                st_now={"phase":"CYCLE_EXPLORATION" if completed<EXPLORE else ("COMPLETE" if completed==TOTAL else "CYCLE_EXPLOITATION"),"round":rnd,"parent_ids":st.get("parent_ids",[])}
                _checkpoint(out,ar,seen,rows,hasher.digest() and jp.read_bytes(),st_now)
                print("CYCLE_CHECKPOINT=%d|JOURNAL_SHA256=%s"%(completed,hasher.hexdigest()),flush=True)
        if completed>=target: break
        if phase=="CYCLE_EXPLORATION" and completed==EXPLORE:
            archive.rebuild(ar); archive.validate(ar)
            parent_ids=scheduler.initial_parent_ids(ar,EXPLOIT)
            if not parent_ids: raise ValueError("NO_ELIGIBLE_PARENTS_AFTER_EXPLORATION")
            st={"phase":"CYCLE_EXPLOITATION","round":0,"parent_ids":parent_ids,"round_items":[],"round_done":0,"exploitation_done":0}
        elif phase=="CYCLE_EXPLOITATION":
            if start+len(items)==start+len(items):
                # Rebuild from durable journal to derive exact next-round state.
                ar,seen,st=_rebuild(rows)
    data=jp.read_bytes() if jp.exists() else b""
    ar,seen,st=_rebuild(rows); archive.rebuild(ar); archive.validate(ar)
    _checkpoint(out,ar,seen,rows,data,st)
    result=_summary(out,ar,seen,rows,data,st)
    rp.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def self_check():
    _ensure()
    ar,seen=_bootstrap()
    ids=scheduler.initial_parent_ids(ar,EXPLOIT)
    if not ids: raise AssertionError("NO_BOOTSTRAP_ELIGIBLE_PARENTS")
    x=orchestrator.exploration_items(4,SEED,0)
    if len(x)!=4 or len({i["strategy"]["strategy_id"] for i in x})!=4: raise AssertionError("EXPLORATION_SELF_CHECK")
    print("V57_V433_QD_CYCLE_RUNNER_V1_SELF_CHECK=PASS|BOOTSTRAP=FROZEN_2048|EXPLORE=1434|EXPLOIT=2662|TOTAL=4096|SEED_BASE=943310|ELIGIBLE_PARENTS=%d|HOLDOUT=UNREAD|ORDERS=DISABLED"%len(ids))
    return True

if __name__=="__main__":
    if "--self-check" in sys.argv: self_check()
    else:
        out=sys.argv[1] if len(sys.argv)>1 else str(ROOT/"work/v433_qd_cycle_4096_execution_v1")
        print("CYCLE_RUN_RESULT="+json.dumps(run(out),sort_keys=True))
