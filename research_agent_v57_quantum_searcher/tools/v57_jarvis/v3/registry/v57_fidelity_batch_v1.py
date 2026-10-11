#!/usr/bin/env python3
import json,sys,datetime
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_proof_v1 as P
STATE=R/'work/autopilot_v433/cumulative_state.json'; ROOT=R/'work/deployment_fidelity_v1'; CP=ROOT/'checkpoint.json'
def main():
 n=max(1,min(int(sys.argv[1]) if len(sys.argv)>1 else 10,50)); x=json.loads(STATE.read_text()); ids=list(x['archive']['exact_backlog']); cp=json.loads(CP.read_text()) if CP.exists() else {'next_index':0,'processed':0,'verified':0,'rejected':0}; start=cp['next_index']; end=min(start+n,len(ids))
 for i in range(start,end):
  sid=ids[i]; e=x['archive']['exact_backlog'][sid]; v=P.G.gate(e); proof={'schema_version':1,'kind':'V57_DEPLOYMENT_FIDELITY_PROOF_V1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'strategy_id':sid,'strategy_sha256':P.hashlib.sha256(P.canon(e['strategy']).encode()).hexdigest(),'verdict':v,'promotion_allowed':bool(v['promotion_allowed']),'holdout_read':False,'september_2026_data_accessed':False,'orders_allowed':False};proof['proof_sha256']=P.hashlib.sha256(P.canon(proof).encode()).hexdigest();P.OUT.mkdir(parents=True,exist_ok=True);(P.OUT/(sid+'.json')).write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n');cp['processed']+=1;cp['verified']+=int(proof['promotion_allowed']);cp['rejected']+=int(not proof['promotion_allowed']);cp['next_index']=i+1
 ROOT.mkdir(parents=True,exist_ok=True);tmp=ROOT/'checkpoint.tmp';tmp.write_text(json.dumps(cp,indent=2,sort_keys=True)+'\n');tmp.replace(CP);print(json.dumps({'status':'PASS','batch_start':start,'batch_end':end,'total':len(ids),**cp,'orders_allowed':False,'holdout_allowed':False},sort_keys=True))
if __name__=='__main__':main()
