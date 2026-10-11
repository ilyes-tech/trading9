import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 s=json.loads((S/"status_v15.json").read_text());a=json.loads((S/"research_agenda_v3.json").read_text());r=json.loads((S/"agenda_replanner_v2.json").read_text());t=json.loads((S/"agenda_terminal_v2.json").read_text());u=json.loads((S/"unattended_acceptance_v7.json").read_text())
 checks={"core_pass":s.get("status")=="PASS","mode_safe_stop":s.get("mode")=="SAFE_STOP_NO_NOVEL_DIRECTION","phase_bounded_stop":s.get("phase")=="EVIDENCE_BOUNDED_SAFE_STOP","agenda_no_active":a.get("active") is None,"agenda_four":len(a.get("items",[]))==4,"agenda_all_exhausted":all(x.get("status")=="EXHAUSTED" for x in a.get("items",[])),"terminal_four":t.get("status")=="AGENDA_EXHAUSTED" and t.get("exhausted_count")==4,"replan_safe_stop":r.get("decision")=="SAFE_STOP","replan_no_proposal":r.get("proposal") is None,"time_not_novel":r.get("novel_time_filter") is False,"acceptance_pass":u.get("status")=="PASS" and u.get("verified_consecutive_cycles")>=3,"market_gates_closed":not any(s.get(k) for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed"))}
 passed=sum(checks.values());total=len(checks);ok=passed==total
 out={"schema_version":9,"kind":"JARVIS_COMPLETION_AUDIT_V9","status":"PASS" if ok else "FAIL","passed":passed,"total":total,"completion_percent":round(100*passed/total,2),"checks":checks,"remaining":[k for k,v in checks.items() if not v]}
 q=S/"completion_audit_v9.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"completion_audit_v9.json")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|COMPLETION_AUDIT_V9|"+str(passed)+"/"+str(total)+"|REMAINING="+str(len(out["remaining"])))
if __name__=="__main__":main()
