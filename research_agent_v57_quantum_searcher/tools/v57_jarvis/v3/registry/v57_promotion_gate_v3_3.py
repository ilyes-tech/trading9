ENGINE="V57_JARVIS_PROMOTION_GATE_V3_3"
SCOPE="DEVELOPMENT_FOLDS_ONLY"
SAFE=("holdout_read","holdout_evaluated","september_2026_data_accessed","orders_allowed","mt5_launch_allowed")
def evaluate(pre_validation,materialized_replay,provenance):
 bad=[]
 if not isinstance(pre_validation,dict): bad.append("PRE_VALIDATION_MISSING")
 if not isinstance(materialized_replay,dict): bad.append("MATERIALIZED_REPLAY_MISSING")
 if not isinstance(provenance,dict): bad.append("PROVENANCE_MISSING")
 if bad: return {"engine":ENGINE,"status":"BLOCKED","scientific_gate_passed":False,"reasons":bad,"promotion_allowed":False,"self_promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
 sid=pre_validation.get("strategy_id")
 if not sid: bad.append("STRATEGY_ID_MISSING")
 if materialized_replay.get("strategy_id")!=sid: bad.append("STRATEGY_ID_MISMATCH_REPLAY")
 if provenance.get("strategy_id")!=sid: bad.append("STRATEGY_ID_MISMATCH_PROVENANCE")
 if pre_validation.get("scope")!=SCOPE: bad.append("BAD_PRE_SCOPE")
 if materialized_replay.get("scope")!=SCOPE: bad.append("BAD_REPLAY_SCOPE")
 if provenance.get("scope")!=SCOPE: bad.append("BAD_PROVENANCE_SCOPE")
 if pre_validation.get("exact_pass") is not True: bad.append("PRE_VALIDATION_NOT_EXACT_PASS")
 if materialized_replay.get("materialized") is not True: bad.append("NOT_MATERIALIZED")
 if materialized_replay.get("exact_pass") is not True: bad.append("MATERIALIZED_REPLAY_NOT_EXACT_PASS")
 if provenance.get("verified") is not True or provenance.get("status")!="PASS": bad.append("PROVENANCE_NOT_VERIFIED")
 hashes=provenance.get("hashes")
 if not isinstance(hashes,dict) or set(hashes)!={"final","deep","plateau","parity","calibration"} or any(not isinstance(v,str) or len(v)!=64 for v in hashes.values()): bad.append("PROVENANCE_HASHES_INVALID")
 for label,obj in (("PRE",pre_validation),("REPLAY",materialized_replay),("PROVENANCE",provenance)):
  for k in SAFE:
   if obj.get(k) is not False: bad.append(label+"_"+k.upper()+"_NOT_FALSE")
 ok=not bad
 return {"engine":ENGINE,"status":"PASS" if ok else "BLOCKED","scientific_gate_passed":ok,"strategy_id":sid,"reasons":bad,"evidence_sha256":hashes if isinstance(hashes,dict) else None,"promotion_allowed":False,"self_promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
