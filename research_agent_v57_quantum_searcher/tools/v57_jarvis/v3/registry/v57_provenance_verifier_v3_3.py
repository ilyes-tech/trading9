import hashlib,json
from pathlib import Path
ENGINE="V57_JARVIS_PROVENANCE_VERIFIER_V3_3"
INTEGRITY=("holdout_read","holdout_evaluated","september_2026_data_accessed")
def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _load(p):
 p=Path(p)
 if not p.is_file(): raise ValueError("EVIDENCE_MISSING:"+str(p))
 return json.loads(p.read_text()),_sha(p)
def verify(final_path,deep_path,plateau_path,parity_path,calibration_path):
 f,fh=_load(final_path); d,dh=_load(deep_path); l,lh=_load(plateau_path); r,rh=_load(parity_path); c,ch=_load(calibration_path); sid=f.get("strategy_id"); bad=[]
 if not sid: bad.append("SID_MISSING")
 if f.get("strategy",{}).get("strategy_id")!=sid: bad.append("SID_FINAL_STRATEGY")
 if l.get("parent_strategy_id")!=sid or l.get("parent_replay",{}).get("strategy_id")!=sid: bad.append("SID_PLATEAU")
 if r.get("strategy_id")!=sid or r.get("runtime_replay",{}).get("strategy_id")!=sid: bad.append("SID_PARITY")
 if c.get("strategy_id")!=sid: bad.append("SID_CALIBRATION")
 if f.get("deep_validation",{}).get("sha256")!=dh: bad.append("DEEP_LINK")
 if f.get("local_plateau",{}).get("sha256")!=lh: bad.append("PLATEAU_LINK")
 if c.get("sources",{}).get("final_survivor_sha256")!=fh: bad.append("FINAL_CAL_LINK")
 if c.get("sources",{}).get("runtime_semantic_parity_sha256")!=rh: bad.append("PARITY_CAL_LINK")
 if f.get("status")!="FROZEN_ENGINEERING_SURVIVOR" or f.get("deep_validation",{}).get("status")!="DEEP_PASS": bad.append("FINAL_STATUS")
 if r.get("status")!="PASS": bad.append("PARITY_STATUS")
 if c.get("status")!="FROZEN_DEMO_CALIBRATION": bad.append("CALIBRATION_STATUS")
 for name,o in (("FINAL",f),("DEEP",d),("PLATEAU",l),("PARITY",r),("CALIBRATION",c)):
  for k in INTEGRITY:
   if o.get("research_integrity",{}).get(k) is not False: bad.append(name+"_"+k)
 return {"engine":ENGINE,"status":"PASS" if not bad else "BLOCKED","verified":not bad,"strategy_id":sid,"reasons":bad,"scope":"DEVELOPMENT_FOLDS_ONLY","hashes":{"final":fh,"deep":dh,"plateau":lh,"parity":rh,"calibration":ch},"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"orders_allowed":False,"mt5_launch_allowed":False}
