#!/usr/bin/env python3
import hashlib,json,sys,datetime
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher'); sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_gate_v1 as G
OUT=R/'work/deployment_fidelity_v1/proofs'
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 x=json.loads(G.STATE.read_text()); b=x['archive']['exact_backlog']; sid=sys.argv[1] if len(sys.argv)>1 else next(iter(b)); e=b[sid]; verdict=G.gate(e)
 proof={'schema_version':1,'kind':'V57_DEPLOYMENT_FIDELITY_PROOF_V1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'strategy_id':sid,'strategy_sha256':hashlib.sha256(canon(e['strategy']).encode()).hexdigest(),'verdict':verdict,'promotion_allowed':bool(verdict['promotion_allowed']),'holdout_read':False,'september_2026_data_accessed':False,'orders_allowed':False}
 proof['proof_sha256']=hashlib.sha256(canon(proof).encode()).hexdigest(); OUT.mkdir(parents=True,exist_ok=True); p=OUT/(sid+'.json'); p.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n'); print('PASS|FIDELITY_PROOF|'+sid+'|PROMOTION='+str(proof['promotion_allowed']).upper()+'|SHA256='+proof['proof_sha256'])
if __name__=='__main__': main()
