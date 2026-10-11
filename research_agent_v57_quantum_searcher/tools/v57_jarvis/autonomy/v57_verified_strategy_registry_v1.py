#!/usr/bin/env python3
import json,sys,hashlib,datetime
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_verify_v1 as V
STATE=R/'work/autopilot_v433/cumulative_state.json'; OUT=R/'work/v57_jarvis/verified_strategy_registry_v1.json'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 x=json.loads(STATE.read_text()); b=x['archive']['exact_backlog']; rows=[]
 for p in sorted(V.PROOFS.glob('*.json')):
  sid=p.stem; ok,reason=V.verify(sid)
  if not ok: continue
  e=b.get(sid); proof=json.loads(p.read_text())
  if not e: continue
  rows.append({'strategy_id':sid,'strategy_sha256':proof['strategy_sha256'],'proof_sha256':proof['proof_sha256'],'fixed_min_stress_pf':proof['verdict'].get('fixed_min_stress_pf'),'market':e['strategy']['market'],'side':e['strategy'].get('market',{}).get('side') or e['strategy'].get('side'),'execution_allowed':False})
 reg={'schema_version':1,'kind':'JARVIS_VERIFIED_STRATEGY_REGISTRY_V1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(rows),'strategies':rows,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False};reg['registry_sha256']=hashlib.sha256(canon(reg).encode()).hexdigest();OUT.parent.mkdir(parents=True,exist_ok=True);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(reg,indent=2,sort_keys=True)+'\n');tmp.replace(OUT);print('PASS|VERIFIED_REGISTRY|COUNT='+str(len(rows))+'|SHA256='+reg['registry_sha256'])
if __name__=='__main__':main()
