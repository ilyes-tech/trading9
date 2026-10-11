#!/usr/bin/env python3
"""Fail-closed, read-only finishing decisions; never authorizes MT5."""
import json, hashlib, sys, time
from pathlib import Path
S = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def read(name):
    p = S / name
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("MISSING_OR_SYMLINK:" + name)
    return json.loads(p.read_text())
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
