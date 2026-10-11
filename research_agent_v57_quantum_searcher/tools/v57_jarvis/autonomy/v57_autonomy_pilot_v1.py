#!/usr/bin/env python3
import json,pathlib,subprocess,sys,time
ROOT=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');A=ROOT/'tools/v57_jarvis/autonomy';S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def run(name):
 p=subprocess.run([sys.executable,str(A/name)],capture_output=True,text=True);return {'name':name,'rc':p.returncode,'ok':p.returncode==0,'out':(p.stdout+p.stderr).strip()[-2000:]}
def main():
 checks=[run('v57_core_freeze_guard_v1.py')]
 if not checks[-1]['ok']: print('STOP|FAIL|AUTONOMY_PILOT|CORE_FREEZE');return 3
 # Guarded-layer manifest is verified without mutating its frozen components.
 layer=ROOT/'work/v57_jarvis/V57_JARVIS_AUTONOMY_GUARDED_LAYER_FREEZE_V1.json'
 if not layer.is_file(): print('STOP|FAIL|AUTONOMY_PILOT|GUARDED_LAYER_MANIFEST_MISSING');return 3
 checks += [run('v57_event_sentinel_v1.py'),run('v57_event_router_v1.py')]
 if not all(x['ok'] for x in checks): print('STOP|FAIL|AUTONOMY_PILOT|OBSERVE_ROUTE');return 3
 route=json.loads((S/'event_router_v1.json').read_text()); action=route.get('action','IDLE'); before=(S/'bounded_objective_v1.json').stat().st_mtime_ns if (S/'bounded_objective_v1.json').is_file() else None; op=run('v57_objective_opener_v1.py'); checks.append(op); after=(S/'bounded_objective_v1.json').stat().st_mtime_ns if (S/'bounded_objective_v1.json').is_file() else None; opened=op['ok'] and after is not None and after!=before
 if not op['ok']: print('STOP|FAIL|AUTONOMY_PILOT|OBJECTIVE_OPENER');return 3
 state='OBJECTIVE_OPENED' if opened else ('IDLE' if action in ('IDLE','OBSERVE','DO_NOT_REPEAT_IDENTICAL_PROBE') else 'REVIEW_REQUIRED')
 out={'schema_version':1,'kind':'JARVIS_AUTONOMY_PILOT_V1','status':'PASS','state':state,'routed_action':action,'objective_opened':opened,'checks':checks,'research_execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()}
 t=S/'autonomy_pilot_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'autonomy_pilot_v1.json')
 print('ALL PASS|AUTONOMY_PILOT_V1|STATE='+state+'|ACTION='+action+'|OBJECTIVE_OPENED='+('YES' if opened else 'NO'));return 0
if __name__=='__main__':sys.exit(main())
