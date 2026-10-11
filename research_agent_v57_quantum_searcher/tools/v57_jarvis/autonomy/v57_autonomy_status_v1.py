import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def load(n):
 p=S/n
 return json.loads(p.read_text()) if p.exists() else {}
def main():
 st=load("status_v2.json");au=load("capability_audit.json");rf=load("reflection_v2.json")
 print("JARVIS_AUTONOMY="+st.get("status","UNKNOWN"))
 print("PHASE="+st.get("phase","UNKNOWN"))
 print("COMPUTE_GATE="+st.get("compute_gate","UNKNOWN"))
 print("MEMORY_OBSERVATIONS="+str(rf.get("observations","UNKNOWN")))
 print("NEXT="+rf.get("next_action",st.get("next_action","UNKNOWN")))
 print("CAPABILITY_GAPS="+str(len(au.get("gaps",[]))))
 print("SEARCHER_ROLE="+au.get("searcher_role","OPTIONAL_TOOL_NOT_CONTROLLER"))
 print("SAFETY=NO_ORDERS|NO_MT5|NO_HOLDOUT|NO_AUTOPROMOTION")
if __name__=="__main__":main()
