import json
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');J=S/'mission_outcomes_v1.jsonl';O=S/'recovery_decision_v1.json'
def decide(kind):
 rows=[json.loads(x) for x in J.read_text().splitlines() if x.strip()] if J.exists() else [];xs=[x for x in rows if x.get('mission_kind')==kind];fails=[x for x in xs if x.get('status')=='FAILURE'];succ=[x for x in xs if x.get('status')=='SUCCESS']
 if fails: action='DIAGNOSE_BEFORE_RETRY';retry=False
 elif succ: action='REUSE_PROVEN_PLAN';retry=True
 else: action='FIRST_RUN_GUARDED';retry=True
 return {'schema_version':1,'kind':'JARVIS_RECOVERY_DECIDER_V1','status':'PASS','mission_kind':kind,'history':len(xs),'successes':len(succ),'failures':len(fails),'decision':action,'retry_allowed':retry,'mutation_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
def main():
 import sys;k=(sys.argv[1] if len(sys.argv)>1 else 'STATUS').upper();o=decide(k);t=O.with_suffix('.tmp');t.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');t.replace(O);print(f"ALL PASS|RECOVERY_DECIDER|KIND={k}|DECISION={o['decision']}|RETRY={str(o['retry_allowed']).upper()}")
if __name__=='__main__':main()
