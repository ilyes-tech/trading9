#!/usr/bin/env python3
"""Persistent fail-closed research scheduler. No trading or search bypass."""
import argparse,json,subprocess,sys,time,fcntl
from pathlib import Path
A=Path(__file__).resolve().parent
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
PY=Path("/home/trading/TradingAI-HF-Lab/.venv-research/bin/python")
def cycle():
    steps=[]
    inventory=subprocess.run([str(PY),str(A/'v57_multimarket_capability_inventory_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_capability_inventory_v1.py','rc':inventory.returncode,'output':(inventory.stdout+inventory.stderr).strip()[-500:]})
    if inventory.returncode:return 'STOP_FAIL',steps
    # Literature triage is advisory only; it cannot authorize search or orders.
    triage=subprocess.run([str(PY),str(A/'v57_evidence_hypothesis_proposer_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_evidence_hypothesis_proposer_v1.py','rc':triage.returncode,'output':(triage.stdout+triage.stderr).strip()[-500:]})
    if triage.returncode:return 'STOP_FAIL',steps
    feasibility=subprocess.run([str(PY),str(A/'v57_hypothesis_feasibility_triage_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_hypothesis_feasibility_triage_v1.py','rc':feasibility.returncode,'output':(feasibility.stdout+feasibility.stderr).strip()[-500:]})
    if feasibility.returncode:return 'STOP_FAIL',steps
    spec=subprocess.run([str(PY),str(A/'v57_bar_proxy_spec_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_bar_proxy_spec_v1.py','rc':spec.returncode,'output':(spec.stdout+spec.stderr).strip()[-500:]})
    if spec.returncode:return 'STOP_FAIL',steps
    queue=subprocess.run([str(PY),str(A/'v57_multimarket_research_queue_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_research_queue_v1.py','rc':queue.returncode,'output':(queue.stdout+queue.stderr).strip()[-500:]})
    if queue.returncode:return 'STOP_FAIL',steps
    novelty=subprocess.run([str(PY),str(A/'v57_multimarket_novelty_review_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_novelty_review_v1.py','rc':novelty.returncode,'output':(novelty.stdout+novelty.stderr).strip()[-500:]})
    if novelty.returncode:return 'STOP_FAIL',steps
    features=subprocess.run([str(PY),str(A/'v57_multimarket_feature_eligibility_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_feature_eligibility_v1.py','rc':features.returncode,'output':(features.stdout+features.stderr).strip()[-500:]})
    if features.returncode:return 'STOP_FAIL',steps
    questions=subprocess.run([str(PY),str(A/'v57_multimarket_question_builder_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_question_builder_v1.py','rc':questions.returncode,'output':(questions.stdout+questions.stderr).strip()[-500:]})
    if questions.returncode:return 'STOP_FAIL',steps
    registry=subprocess.run([str(PY),str(A/'v57_multimarket_candidate_registry_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_candidate_registry_v1.py','rc':registry.returncode,'output':(registry.stdout+registry.stderr).strip()[-500:]})
    if registry.returncode:return 'STOP_FAIL',steps
    feedback=subprocess.run([str(PY),str(A/'v57_multimarket_research_feedback_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_research_feedback_v1.py','rc':feedback.returncode,'output':(feedback.stdout+feedback.stderr).strip()[-500:]})
    if feedback.returncode:return 'STOP_FAIL',steps
    decision=subprocess.run([str(PY),str(A/'v57_multimarket_decision_v1.py')],capture_output=True,text=True,timeout=60)
    steps.append({'script':'v57_multimarket_decision_v1.py','rc':decision.returncode,'output':(decision.stdout+decision.stderr).strip()[-500:]})
    if decision.returncode:return 'STOP_FAIL',steps
    for name in ("v57_finishing_decisions_v1.py","v57_mt5_package_readiness_v1.py","v57_mt5_dsl_mapping_guard_v1.py","v57_review_evidence_manifest_v1.py","v57_phase2_handoff_guard_v1.py","v57_research_orchestration_bridge_v2.py","v57_tool_selector_v1.py","v57_search_authorization_gate_v1.py"):
        p=subprocess.run([str(PY),str(A/name)],capture_output=True,text=True,timeout=180)
        steps.append({"script":name,"rc":p.returncode,"output":(p.stdout+p.stderr).strip()[-500:]})
        if p.returncode and name!="v57_search_authorization_gate_v1.py":
            return "STOP_FAIL",steps
    try:
        handoff=json.loads((S/"phase2_handoff_guard_v1.json").read_text())
    except (OSError,ValueError):
        return "STOP_FAIL",steps
    if handoff.get("status")=="ELIGIBLE_FOR_TRIAGE":
        return "SAFE_IDLE",steps
    if handoff.get("status")!="BLOCKED":return "STOP_FAIL",steps
    # Phase 2 supervisor is the sole owner of its guarded research chain.
    # Only an existing verified binding with a fresh unconsumed token may start it.
    try:
        binding=json.loads((S/"phase2_contract_execution_binding_v1.json").read_text())
        ledger=json.loads((S/"search_execution_ledger_v1.json").read_text())
        scientific=json.loads((S/"phase2_scientific_execution_ledger_v1.json").read_text())
        gate_doc=json.loads((S/"search_execution_gate_v1.json").read_text())
    except (OSError,ValueError):
        binding={};ledger={};scientific={};gate_doc={}
    token=(binding.get("binding") or {}).get("execution_token")
    if binding.get("status")=="BOUND" and binding.get("execution_verified") is True:
        try:
            current_auth=json.loads((S/"search_authorization_v1.json").read_text())
            current_objective=json.loads((S/"bounded_objective_v1.json").read_text())
        except (OSError,ValueError):return "SAFE_IDLE",steps
        if current_auth.get("authorized") is not True or current_auth.get("execution_started") is not False:return "SAFE_IDLE",steps
        if current_auth.get("max_candidates")!=gate_doc.get("budget_candidates") or not 1<=gate_doc.get("budget_candidates",0)<=4:return "SAFE_IDLE",steps
        if current_objective.get("objective_id")!=gate_doc.get("objective_id"):return "SAFE_IDLE",steps
        if not isinstance(token,str) or len(token)!=64 or gate_doc.get("ready") is not True or gate_doc.get("execution_token")!=token:return "STOP_FAIL",steps
        if token in (ledger.get("consumed_tokens") or []) or token in (scientific.get("completed_tokens") or []):return "SAFE_IDLE",steps
        phase2=subprocess.run([str(PY),str(A/"v57_phase2_supervisor_v1.py")],capture_output=True,text=True,timeout=1800)
        steps.append({"script":"v57_phase2_supervisor_v1.py","rc":phase2.returncode,"output":(phase2.stdout+phase2.stderr).strip()[-500:]})
        return ("PHASE2_COMPLETED" if phase2.returncode==0 else "STOP_FAIL"),steps
    try:
        auth=json.loads((S/"search_authorization_v1.json").read_text())
    except (OSError,ValueError):
        return "STOP_FAIL",steps
    if auth.get("authorized") is True:
        gate=subprocess.run([str(PY),str(A/"v57_search_execution_gate_v1.py")],capture_output=True,text=True,timeout=60)
        steps.append({"script":"v57_search_execution_gate_v1.py","rc":gate.returncode,"output":(gate.stdout+gate.stderr).strip()[-500:]})
        if gate.returncode:return "STOP_FAIL",steps
        execution=json.loads((S/"search_execution_gate_v1.json").read_text())
        if execution.get("ready") is not True or not 1<=execution.get("budget_candidates",0)<=4:return "STOP_FAIL",steps
        executor=subprocess.run([str(PY),str(A/"v57_scientist_v4_execution_binding_v1.py")],capture_output=True,text=True,timeout=1800)
        steps.append({"script":"v57_scientist_v4_execution_binding_v1.py","rc":executor.returncode,"output":(executor.stdout+executor.stderr).strip()[-500:]})
        if executor.returncode:return "STOP_FAIL",steps
        return "RESEARCH_CYCLE_COMPLETED",steps
    if auth.get("status")!="DENIED" or auth.get("max_candidates")!=0:
        return "STOP_FAIL",steps
    return "SAFE_IDLE",steps
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--interval",type=int,default=900)
    args=ap.parse_args()
    if not 60<=args.interval<=86400:raise SystemExit("STOP|FAIL|BAD_INTERVAL")
    S.mkdir(parents=True,exist_ok=True)
    with (S/"research_continuous_runner_v1.lock").open("w") as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit("STOP|FAIL|ALREADY_RUNNING")
        while True:
            try:status,steps=cycle()
            except Exception as e:status,steps="STOP_FAIL",[{"error":type(e).__name__+":"+str(e)}]
            search_executed=status in ("PHASE2_COMPLETED","RESEARCH_CYCLE_COMPLETED")
            doc={"kind":"JARVIS_RESEARCH_CONTINUOUS_RUNNER_V1","status":status,"checked_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"steps":steps,"search_executed":search_executed,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
            temp=S/"research_continuous_runner_v1.tmp"
            temp.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
            temp.replace(S/"research_continuous_runner_v1.json")
            print(("ALL PASS" if status!="STOP_FAIL" else "STOP|FAIL")+"|CONTINUOUS_RUNNER|"+status+"|SEARCH_EXECUTED="+("YES" if search_executed else "NO")+"|ORDERS=NO",flush=True)
            if status=="STOP_FAIL":
                raise SystemExit(3)
            if args.once:break
            time.sleep(args.interval)
if __name__=="__main__":main()
