import hashlib,json,time
from pathlib import Path
ENGINE="V57_JARVIS_EXPERIMENT_LEDGER_V3"
STATE=Path(__file__).resolve().parents[1]/"state"
ALLOWED={"HYPOTHESIS","EXPERIMENT","NEGATIVE_RESULT","EVIDENCE","VALIDATED_FACT"}
def record(kind,payload):
    if kind not in ALLOWED: raise ValueError("BAD_KIND")
    STATE.mkdir(parents=True,exist_ok=True)
    body={"schema_version":1,"kind":kind,"ts_ns":time.time_ns(),"payload":payload}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    body["proof_sha256"]=hashlib.sha256(raw).hexdigest()
    p=STATE/"experiment_ledger_v3.jsonl"
    with p.open("a",encoding="utf-8") as f: f.write(json.dumps(body,sort_keys=True,ensure_ascii=False)+"\n")
    return {"status":"STORED","kind":kind,"proof_sha256":body["proof_sha256"]}
def read_all():
    p=STATE/"experiment_ledger_v3.jsonl"
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def record_result(candidate_id,status,reason=None,proof_sha256=None,exact_pass=False):
    kind="EVIDENCE" if exact_pass is True and status in ("PASS","VALIDATED","EVALUATED") else "NEGATIVE_RESULT"
    return record(kind,{"candidate_id":str(candidate_id),"status":str(status),"reason":reason,"proof_sha256":proof_sha256,"exact_pass":bool(exact_pass)})
