import hashlib,json
from pathlib import Path
ENGINE="V57_JARVIS_PROMOTION_GATE_V3_2"
ALLOWED_SCOPE="DEVELOPMENT_FOLDS_ONLY"
def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _load(path,expected_sha=None):
    p=Path(path)
    if not p.is_file(): raise ValueError("EVIDENCE_MISSING")
    got=_sha(p)
    if expected_sha is not None and got!=str(expected_sha): raise ValueError("EVIDENCE_HASH_MISMATCH")
    return json.loads(p.read_text()),got
def evaluate(pre_validation,materialized_replay,provenance):
    reasons=[]
    if not isinstance(pre_validation,dict): reasons.append("PRE_VALIDATION_MISSING")
    if not isinstance(materialized_replay,dict): reasons.append("MATERIALIZED_REPLAY_MISSING")
    if not isinstance(provenance,dict): reasons.append("PROVENANCE_MISSING")
    sid=None
    if not reasons:
        sid=pre_validation.get("strategy_id")
        if not sid: reasons.append("STRATEGY_ID_MISSING")
        if materialized_replay.get("strategy_id")!=sid: reasons.append("STRATEGY_ID_MISMATCH_REPLAY")
        if provenance.get("strategy_id")!=sid: reasons.append("STRATEGY_ID_MISMATCH_PROVENANCE")
        if pre_validation.get("scope")!=ALLOWED_SCOPE: reasons.append("BAD_PRE_SCOPE")
        if materialized_replay.get("scope")!=ALLOWED_SCOPE: reasons.append("BAD_REPLAY_SCOPE")
        if pre_validation.get("exact_pass") is not True: reasons.append("PRE_VALIDATION_NOT_EXACT_PASS")
        if materialized_replay.get("exact_pass") is not True: reasons.append("MATERIALIZED_REPLAY_NOT_EXACT_PASS")
        if materialized_replay.get("materialized") is not True: reasons.append("NOT_MATERIALIZED")
        if provenance.get("verified") is not True: reasons.append("PROVENANCE_NOT_VERIFIED")
        for obj,label in ((pre_validation,"PRE"),(materialized_replay,"REPLAY"),(provenance,"PROVENANCE")):
            if obj.get("holdout_read") is not False: reasons.append(label+"_HOLDOUT_NOT_FALSE")
            if obj.get("orders_allowed") is not False: reasons.append(label+"_ORDERS_NOT_FALSE")
            if obj.get("mt5_launch_allowed") is not False: reasons.append(label+"_MT5_NOT_FALSE")
    allowed=not reasons
    return {"engine":ENGINE,"status":"PASS" if allowed else "BLOCKED","strategy_id":sid,"reasons":reasons,"scientific_gate_passed":allowed,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False,"self_promotion_allowed":False}
def evaluate_files(pre_path,pre_sha,replay_path,replay_sha,provenance_path,provenance_sha):
    pre,ph=_load(pre_path,pre_sha); replay,rh=_load(replay_path,replay_sha); prov,vh=_load(provenance_path,provenance_sha)
    out=evaluate(pre,replay,prov); out["evidence_sha256"]={"pre_validation":ph,"materialized_replay":rh,"provenance":vh}; return out
