#!/usr/bin/env python3
import json,sys,hashlib,datetime
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_verify_v1 as V
REG=R/'work/v57_jarvis/verified_strategy_registry_v1.json';OUT=R/'work/v57_jarvis/dynamic_verified_pool_v1.json'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 reg=json.loads(REG.read_text()); active=[];revoked=[]
 for z in reg['strategies']:
  ok,reason=V.verify(z['strategy_id'])
  if ok: active.append({**z,'execution_allowed':False})
  else: revoked.append({'strategy_id':z['strategy_id'],'reason':reason})
 pool={'schema_version':1,'kind':'JARVIS_DYNAMIC_VERIFIED_POOL_V1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_registry_sha256':reg['registry_sha256'],'active_count':len(active),'revoked_count':len(revoked),'active':active,'revoked':revoked,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
 pool['pool_sha256']=hashlib.sha256(canon(pool).encode()).hexdigest();OUT.parent.mkdir(parents=True,exist_ok=True);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(pool,indent=2,sort_keys=True)+'\n');tmp.replace(OUT);print('PASS|DYNAMIC_POOL|ACTIVE='+str(len(active))+'|REVOKED='+str(len(revoked))+'|SHA256='+pool['pool_sha256'])
if __name__=='__main__':main()
