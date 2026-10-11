import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 probe=json.loads((S/"price_action_result_v1.json").read_text());verify=json.loads((S/"price_action_fidelity_verify_v2.json").read_text());pre=json.loads((S/"price_action_preflight_v1.json").read_text())
 if probe.get("status")!="COMPLETED" or verify.get("status")!="PASS" or pre.get("status")!="PASS":raise RuntimeError("EVIDENCE_INCOMPLETE")
 records=probe["result"]["records"];evaluated=sum(x.get("status")=="EVALUATED" for x in records);initial=sum(isinstance(x.get("result"),dict) and x["result"].get("exact_pass") is True for x in records)
 if len(records)!=4 or evaluated!=3 or initial!=2 or verify.get("checked")!=initial:raise RuntimeError("COUNT_MISMATCH")
 passed=sum(x.get("deployment_evidence_pass") is True for x in verify["results"])
 if passed:raise RuntimeError("UNEXPECTED_DEPLOYMENT_EVIDENCE_REQUIRES_REVIEW")
 feedback={"schema_version":1,"kind":"V57_PRICE_ACTION_FEEDBACK_V1","status":"COMPLETED","capability":"price_action","evaluated":evaluated,"prefilter_rejected":len(records)-evaluated,"initial_exact_pass":initial,"deployment_evidence_pass":passed,"verdict":"NO_DEPLOYMENT_EVIDENCE","next_action":"SAFE_STOP_PENDING_NEW_EVIDENCE","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"sources":["price_action_result_v1.json","price_action_fidelity_verify_v2.json"]}
 agenda={"schema_version":1,"kind":"V57_CAPABILITY_AGENDA_V5","status":"SAFE_STOP","capability":"price_action","state":"EXHAUSTED_FOR_CURRENT_PROBE","reason":"NO_DEPLOYMENT_EVIDENCE","repeat_same_probe_allowed":False,"new_research_requires":"NEW_EVIDENCE_BACKED_CAUSAL_HYPOTHESIS","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 for name,data in [("price_action_feedback_v1.json",feedback),("capability_agenda_v5.json",agenda)]:
  q=S/(name+".tmp");q.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n");q.replace(S/name)
 print("ALL PASS|PRICE_ACTION_FEEDBACK_V1|EVALUATED=3|INITIAL_PASS=2|DEPLOYMENT_PASS=0|NEXT=SAFE_STOP")
 print("ALL PASS|CAPABILITY_AGENDA_V5|price_action=EXHAUSTED_FOR_CURRENT_PROBE|REPEAT=FALSE")
if __name__=="__main__":main()
