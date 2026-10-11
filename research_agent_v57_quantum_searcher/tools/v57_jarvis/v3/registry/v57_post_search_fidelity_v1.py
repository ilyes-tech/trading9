#!/usr/bin/env python3
import json,sys,hashlib,datetime,os
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher'); LAB=R.parent
os.chdir(LAB); sys.path.insert(0,str(R/'tools/v57_jarvis/v3/registry'))
import v57_deployment_fidelity_proof_v1 as P
import v57_deployment_fidelity_verify_v1 as V
import importlib.util
_ADMISSION=R/'tools/v57_jarvis/autonomy/v57_searcher_admission_v1.py'
def _verify_entry_proof(entry,proof):
 spec=importlib.util.spec_from_file_location('fidelity_record_admission',_ADMISSION); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 sid=entry['strategy']['strategy_id']
 record={'status':'EVALUATED','strategy':entry['strategy'],'result':{'exact_pass':True},'post_search_fidelity':{'strategy_id':sid,'deployment_exact_pass':True,'strategy_sha256':proof.get('strategy_sha256'),'proof_sha256':proof.get('proof_sha256')}}
 return module.verify_record_proof(record)
STATE=R/'work/autopilot_v433/cumulative_state.json'; OUT=R/'work/post_search_fidelity_v1'
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def _entry_from_record(record):
 if not isinstance(record,dict) or record.get('status')!='EVALUATED' or not isinstance(record.get('result'),dict) or record['result'].get('exact_pass') is not True: return None
 result=record['result']; folds=result.get('folds')
 if not isinstance(folds,list) or len(folds)!=3 or not all(f.get('pass') is True for f in folds): return None
 return {'strategy':record['strategy'],'meta':record.get('meta'),'exact_pass':True,'objectives':{'min_stress_pf':result.get('min_stress_pf'),'min_base_pf':result.get('min_base_pf')},'support':{'min_selected_trades':min(int(f.get('selected_trades',0)) for f in folds)}}
def _qualify_entry(e):
 if not e or e.get('exact_pass') is not True: return {'status':'REJECTED','reason':'NOT_SEARCH_EXACT'}
 s=e['strategy']; sid=s['strategy_id']; sh=hashlib.sha256(canon(s).encode()).hexdigest(); proof_path=V.PROOFS/(sid+'.json'); reusable=False
 if proof_path.exists():
  old=json.loads(proof_path.read_text()); reusable=old.get('strategy_sha256')==sh and old.get('proof_sha256')==hashlib.sha256(canon({k:v for k,v in old.items() if k!='proof_sha256'}).encode()).hexdigest()
 if not reusable:
  verdict=P.G.gate(e); proof={'schema_version':1,'kind':'V57_DEPLOYMENT_FIDELITY_PROOF_V1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'strategy_id':sid,'strategy_sha256':sh,'verdict':verdict,'promotion_allowed':bool(verdict['promotion_allowed']),'holdout_read':False,'september_2026_data_accessed':False,'orders_allowed':False}; proof['proof_sha256']=hashlib.sha256(canon(proof).encode()).hexdigest(); V.PROOFS.mkdir(parents=True,exist_ok=True); tmp=proof_path.with_suffix('.tmp'); tmp.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n'); tmp.replace(proof_path)
 proof=json.loads(proof_path.read_text()); ok,reason=_verify_entry_proof(e,proof); a=e.get('objectives',{}).get('min_stress_pf'); z=proof.get('verdict',{}).get('fixed_min_stress_pf')
 result={'schema_version':1,'kind':'V57_POST_SEARCH_FIDELITY_V1','strategy_id':sid,'search_exact_pass':True,'deployment_exact_pass':bool(ok),'classification':'DEPLOYMENT_EXACT' if ok else 'DEPLOYMENT_REJECTED','verify_reason':reason,'search_min_stress_pf':a,'fixed_min_stress_pf':z,'pf_delta':z-a if isinstance(a,(int,float)) and isinstance(z,(int,float)) else None,'strategy_sha256':sh,'proof_sha256':proof.get('proof_sha256'),'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
 OUT.mkdir(parents=True,exist_ok=True); dst=OUT/(sid+'.json'); tmp=dst.with_suffix('.tmp'); tmp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); tmp.replace(dst); return result
def qualify(sid):
 x=json.loads(STATE.read_text()); e=x['archive']['exact_backlog'].get(sid); r=_qualify_entry(e); r.setdefault('strategy_id',sid); return r
def qualify_record(record):
 e=_entry_from_record(record); sid=record.get('strategy',{}).get('strategy_id') if isinstance(record,dict) else None
 if e is None: return {'status':'REJECTED','reason':'NOT_SEARCH_EXACT_RECORD','strategy_id':sid,'deployment_exact_pass':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
 return _qualify_entry(e)
def main():
 if len(sys.argv)!=2: raise SystemExit('USAGE: v57_post_search_fidelity_v1.py STRATEGY_ID')
 r=qualify(sys.argv[1]); print(json.dumps(r,sort_keys=True)); raise SystemExit(0 if r.get('deployment_exact_pass') else 4)
if __name__=='__main__': main()
