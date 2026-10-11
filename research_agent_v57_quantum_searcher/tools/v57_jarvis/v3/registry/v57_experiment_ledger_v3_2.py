import fcntl,hashlib,json,os,time
from pathlib import Path
ENGINE="V57_JARVIS_EXPERIMENT_LEDGER_V3_2"
STATE=Path(__file__).resolve().parents[1]/"state"
LEDGER=STATE/"experiment_ledger_v3_2.jsonl"
ALLOWED={"HYPOTHESIS","EXPERIMENT","NEGATIVE_RESULT","EVIDENCE","VALIDATED_FACT"}
def _canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _proof(body): return hashlib.sha256(_canon(body)).hexdigest()
def _verify_row(row,expected_prev):
    if row.get("prev_sha256")!=expected_prev: raise ValueError("CHAIN_MISMATCH")
    proof=row.get("proof_sha256"); body={k:v for k,v in row.items() if k!="proof_sha256"}
    if proof!=_proof(body): raise ValueError("PROOF_MISMATCH")
    return proof
def verify():
    if not LEDGER.exists(): return {"status":"PASS","rows":0,"head":None}
    prev=None; n=0
    with LEDGER.open("r",encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row=json.loads(line); n+=1
            if row.get("sequence")!=n: raise ValueError("SEQUENCE_MISMATCH")
            prev=_verify_row(row,prev)
    return {"status":"PASS","rows":n,"head":prev}
def record(kind,payload):
    if kind not in ALLOWED: raise ValueError("BAD_KIND")
    if not isinstance(payload,dict): raise ValueError("BAD_PAYLOAD")
    if kind=="VALIDATED_FACT":
        if payload.get("scientific_gate_passed") is not True: raise ValueError("VALIDATED_FACT_REQUIRES_SCIENTIFIC_GATE")
        if payload.get("exact_pass") is not True: raise ValueError("VALIDATED_FACT_REQUIRES_EXACT_PASS")
        if payload.get("status") not in ("PASS","VALIDATED","EVALUATED"): raise ValueError("VALIDATED_FACT_BAD_STATUS")
        h=payload.get("evidence_sha256")
        if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdefABCDEF" for c in h): raise ValueError("VALIDATED_FACT_REQUIRES_EVIDENCE_SHA256")
        g=payload.get("gate_evidence_sha256")
        if not isinstance(g,str) or len(g)!=64 or any(c not in "0123456789abcdefABCDEF" for c in g): raise ValueError("VALIDATED_FACT_REQUIRES_GATE_SHA256")
        if not isinstance(payload.get("provenance"),dict) or payload["provenance"].get("verified") is not True: raise ValueError("VALIDATED_FACT_REQUIRES_PROVENANCE")
    STATE.mkdir(parents=True,exist_ok=True)
    with LEDGER.open("a+",encoding="utf-8") as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX); f.seek(0); lines=[x for x in f.read().splitlines() if x.strip()]; prev=None
        for i,line in enumerate(lines,1):
            row=json.loads(line)
            if row.get("sequence")!=i: raise ValueError("SEQUENCE_MISMATCH")
            prev=_verify_row(row,prev)
        body={"schema_version":2,"engine":ENGINE,"sequence":len(lines)+1,"kind":kind,"ts_ns":time.time_ns(),"prev_sha256":prev,"payload":payload}; body["proof_sha256"]=_proof(body); f.seek(0,os.SEEK_END); f.write(json.dumps(body,sort_keys=True,ensure_ascii=False)+"\n"); f.flush(); os.fsync(f.fileno()); fcntl.flock(f.fileno(),fcntl.LOCK_UN)
    return {"status":"STORED","kind":kind,"sequence":body["sequence"],"proof_sha256":body["proof_sha256"]}
def read_all():
    verify()
    if not LEDGER.exists(): return []
    return [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]
def record_result(candidate_id,status,reason=None,evidence_sha256=None,exact_pass=False,scientific_gate_passed=False,provenance=None):
    payload={"candidate_id":str(candidate_id),"status":str(status),"reason":reason,"evidence_sha256":evidence_sha256,"exact_pass":bool(exact_pass),"scientific_gate_passed":bool(scientific_gate_passed),"provenance":provenance}
    kind="VALIDATED_FACT" if scientific_gate_passed is True else ("EVIDENCE" if exact_pass is True and status in ("PASS","VALIDATED","EVALUATED") else "NEGATIVE_RESULT")
    return record(kind,payload)
