#!/usr/bin/env python3
import json,hashlib,datetime,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_verify_v1 as V
REG=R/'work/v57_jarvis/verified_strategy_registry_v1.json'; AUD=R/'work/v57_jarvis/verified_registry_audit_v1.jsonl'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 x=json.loads(REG.read_text()); h=x.get('registry_sha256'); q=dict(x);q.pop('registry_sha256',None);assert hashlib.sha256(canon(q).encode()).hexdigest()==h
 valid=[];revoked=[]
 for z in x['strategies']:
  ok,reason=V.verify(z['strategy_id']); (valid if ok else revoked).append({'strategy_id':z['strategy_id'],'reason':reason})
 event={'ts':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'VERIFIED_REGISTRY_AUDIT_V1','registry_sha256':h,'count':x['count'],'valid':len(valid),'revoked':revoked,'orders_allowed':False,'mt5_allowed':False}
 prev='0'*64
 if AUD.exists():
  lines=[y for y in AUD.read_text().splitlines() if y.strip()]
  if lines: prev=json.loads(lines[-1])['event_sha256']
 event['prev_sha256']=prev;event['event_sha256']=hashlib.sha256(canon(event).encode()).hexdigest();AUD.parent.mkdir(parents=True,exist_ok=True);open(AUD,'a').write(json.dumps(event,sort_keys=True)+'\n');print('PASS|REGISTRY_AUDIT|VALID='+str(len(valid))+'|REVOKED='+str(len(revoked))+'|CHAIN='+event['event_sha256'])
if __name__=='__main__':main()
