#!/usr/bin/env python3
"""Fail-closed, read-only finishing decisions; never authorizes MT5."""
import json, hashlib, sys, time, runpy
from pathlib import Path
S = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def read(name):
    p = S / name
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("MISSING_OR_SYMLINK:" + name)
    return json.loads(p.read_text())
def archived_survivor_decision():
    """Reuse existing forensic tool: a frozen engineering pass is not deployment."""
    existing=Path(__file__).resolve().parent.parent/'registry/v57_strategy_forensics_v2.py'
    if not existing.is_file() or existing.is_symlink():
        raise RuntimeError('ARCHIVED_SURVIVOR_FORENSICS_MISSING')
    result=runpy.run_path(str(existing))['inspect']()
    post=result.get('post_calibration_performance_replay') or {}
    if (result.get('status')!='COMPLETED'
            or result.get('same_strategy_id') is not True
            or result.get('provenance_all_pass') is not True
            or result.get('full_development_calibration',{}).get('proven') is not True
            or post.get('evidence_found') is not True
            or post.get('evidence_valid') is not True
            or post.get('scope')!='DEVELOPMENT_FOLDS_ONLY'
            or result.get('orders_allowed') is not False
            or result.get('mt5_launch_allowed') is not False
            or result.get('holdout_read') is not False):
        raise RuntimeError('ARCHIVED_SURVIVOR_EVIDENCE_NOT_VERIFIED')
    sid=result.get('strategy_id')
    if not isinstance(sid,str) or len(sid)!=64:
        raise RuntimeError('ARCHIVED_SURVIVOR_ID_INVALID')
    conclusion=post.get('conclusion')
    if conclusion=='POST_CALIBRATION_REPLAY_FAIL':
        decision='REJECT_POST_CALIBRATION_REPLAY'
    elif conclusion=='POST_CALIBRATION_REPLAY_PASS':
        decision='EXTERNAL_SCIENTIFIC_REVIEW_REQUIRED_NOT_AUTHORIZED'
    else:
        raise RuntimeError('ARCHIVED_SURVIVOR_POSTCAL_VERDICT_UNKNOWN')
    return {'strategy_id':sid,'decision':decision,
            'engineering_reference_only':True,'scientific_admission':False,
            'initial_technical_deep_pass':True,
            'post_calibration_conclusion':conclusion,
            'post_calibration_evidence_sha256':post['sha256'],
            'post_calibration_fixed_exact_pass':post['fixed_replay'].get('exact_pass'),
            'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}


def main():
    probe = read("price_action_result_v1.json")
    fidelity = read("price_action_fidelity_verify_v2.json")
    deep = read("targeted_existing_candidates_deep_v1.json")
    if probe.get("status") != "COMPLETED" or fidelity.get("status") != "PASS" or deep.get("status") != "COMPLETED":
        raise RuntimeError("SOURCE_STATUS_INVALID")
    checks = {r["strategy_id"]: r for r in fidelity["results"]}
    rows = []
    for record in probe["result"]["records"]:
        sid = record["strategy"]["strategy_id"]
        exact = (record.get("result") or {}).get("exact_pass")
        check = checks.get(sid)
        if exact is True:
            if not check or not all(check.get(k) is True for k in ("proof_hash_valid", "strategy_hash_valid", "integrity_valid")):
                raise RuntimeError("FIDELITY_PROOF_INCOMPLETE:" + sid)
            stage = "DEPLOYMENT_EVIDENCE_REVIEW" if check.get("deployment_evidence_pass") is True else "REJECT_FIDELITY"
        else:
            stage = "REJECT_PREFILTER" if record.get("status") == "PREFILTER_REJECT" else "REJECT_INITIAL"
        rows.append({"strategy_id": sid, "decision": stage, "initial_exact_pass": exact, "deployment_evidence_pass": bool(check and check.get("deployment_evidence_pass") is True)})
    for record in deep["results"]:
        stage = "REJECT_DEEP" if record.get("status") == "DEEP_REJECT" else "MANUAL_EVIDENCE_REVIEW"
        rows.append({"strategy_id": record["strategy_id"], "decision": stage, "replay_exact_pass": record.get("replay_exact_pass")})
    rows.append(archived_survivor_decision())
    ids = [r["strategy_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("DUPLICATE_STRATEGY_ID")
    doc = {"kind": "JARVIS_FINISHING_DECISIONS_V1", "status": "PASS", "checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "examined": len(rows), "deployment_ready_count": 0, "decisions": rows, "orders_allowed": False, "mt5_allowed": False, "auto_promotion_allowed": False, "research_only": True, "note": "Evidence review is not MT5 deployment authorization"}
    target = S / "finishing_decisions_v1.json"
    temp = S / "finishing_decisions_v1.tmp"
    temp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    temp.replace(target)
    print("ALL PASS|FINISHING_DECISIONS|EXAMINED=" + str(len(rows)) + "|READY=0|ORDERS=NO")
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STOP|FAIL|FINISHING_DECISIONS|" + type(exc).__name__ + ":" + str(exc))
        sys.exit(3)
