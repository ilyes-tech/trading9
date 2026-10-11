import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(fn,name):
    s=importlib.util.spec_from_file_location(name,HERE/fn); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
SCI=load("v57_scientist_v3.py","j57v3science")
LEDGER=load("v57_experiment_ledger_v3.py","j57v3ledger_loop")
def run(hypothesis,start=0,count=4):
    if count<1 or count>16: raise ValueError("COUNT_LIMIT")
    out=[]
    for i in range(start,start+count):
        r=SCI.experiment(hypothesis,i,1,True)
        z=r["result"]; rec=z["records"][0] if z.get("records") else {}
        cid=z["candidate_ids"][0]
        status=rec.get("status","UNKNOWN"); exact_pass=bool((rec.get("result") or {}).get("exact_pass",False))
        reason=(rec.get("prefilter") or {}).get("reason") or rec.get("error")
        LEDGER.record_result(cid,status,reason,z.get("proof_sha256"),exact_pass)
        out.append({"candidate_id":cid,"index":i,"status":status,"reason":reason,"ranked":cid in z.get("ranked_candidate_ids",[]),"exact_pass":exact_pass})
    ranked=[x for x in out if x["ranked"] and x["exact_pass"]]
    return {"engine":"V57_JARVIS_SCIENCE_LOOP_V3","status":"COMPLETED","tested":len(out),"ranked_count":len(ranked),"results":out,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
