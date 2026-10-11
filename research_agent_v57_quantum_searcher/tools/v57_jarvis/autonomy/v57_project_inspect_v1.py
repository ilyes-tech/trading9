#!/usr/bin/env python3
import json,pathlib,subprocess,sys
R=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');A=R/'tools/v57_jarvis/autonomy';S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');FINAL=R/'tools/v57_jarvis/v3/V57_JARVIS_V36_POST_SEARCH_FINAL_FREEZE_20261004.json';PF=R/'tools/v57_jarvis/v3/registry/v57_post_search_fidelity_v1.py';ADM=A/'v57_searcher_admission_v1.py'
def load(p):
 try:return json.loads(p.read_text())
 except Exception:return {}
def main():
 freezes=[]
 for n in ('ACTION_FEEDBACK_LOOP_V2_FREEZE.json','CAUSAL_AUTONOMY_BRIDGE_V1_FREEZE.json','JARVIS_RUNTIME_ACCEPTANCE_V1_FREEZE.json','JARVIS_GLOBAL_FINAL_FREEZE_V1.json'):
  x=load(A/n);freezes.append({'name':n,'status':x.get('status','MISSING')})
 g=load(S/'goal_queue_v2.json');acc=load(S/'unattended_acceptance_v3.json');guard=subprocess.run([sys.executable,str(A/'v57_global_autonomy_freeze_guard_v1.py')],text=True,capture_output=True,timeout=30)
 goals=g.get('goals',[]);done=sum(1 for x in goals if x.get('status')=='DONE')
 o={'schema_version':1,'kind':'JARVIS_PROJECT_INSPECT_V1','status':'PASS' if guard.returncode==0 else 'FAIL','project':str(R),'evidence':{'freezes':freezes,'goals_done':done,'goals_total':len(goals),'active_goal':g.get('active_goal'),'autonomous_cycles':acc.get('verified_consecutive_cycles'),'acceptance_status':acc.get('status'),'global_guard_rc':guard.returncode,'global_guard_tail':guard.stdout.strip().splitlines()[-1] if guard.stdout.strip() else ''},'remaining':['Exercer JARVIS V3.6 sur des missions réelles de recherche et n’ouvrir une nouvelle version de développement qu’en cas de défaut reproduit'],'next_priority':'Utiliser l’agent research-only gelé sur des missions réelles et préserver la frontière validée Searcher→Post-Search Fidelity→Admission.','post_search_fidelity_ready':PF.exists(),'searcher_admission_ready':ADM.exists(),'post_search_final_freeze_ready':FINAL.exists(),'read_only':True,'execution':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 print(json.dumps(o,ensure_ascii=False,sort_keys=True));return 0 if o['status']=='PASS' else 3
if __name__=='__main__':sys.exit(main())
