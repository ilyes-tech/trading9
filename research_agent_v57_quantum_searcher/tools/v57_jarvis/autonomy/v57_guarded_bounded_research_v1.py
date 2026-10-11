#!/usr/bin/env python3
import json,pathlib,subprocess,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');A=pathlib.Path(__file__).resolve().parent
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 g=load('search_execution_gate_v1.json')
 if g.get('ready') is not True or g.get('search_process_started') is not False: print('STOP|FAIL|GUARDED_BOUNDED_RESEARCH|EXEC_GATE_NOT_READY');return 3
 tok=g.get('execution_token');budget=g.get('budget_candidates');
 if not tok or not isinstance(budget,int) or not 1<=budget<=4: print('STOP|FAIL|GUARDED_BOUNDED_RESEARCH|INVALID_TOKEN_OR_BUDGET');return 3
 # Consume token atomically before any child process can start.
 led=load('search_execution_ledger_v1.json');used=list(led.get('consumed_tokens') or [])
 if tok in used: print('STOP|FAIL|GUARDED_BOUNDED_RESEARCH|TOKEN_REPLAY');return 3
 used.append(tok);tmp=S/'search_execution_ledger_v1.tmp';tmp.write_text(json.dumps({'schema_version':1,'consumed_tokens':used},indent=2,sort_keys=True)+'\n');tmp.replace(S/'search_execution_ledger_v1.json')
 # Phase-2 integration test remains dry-run: prove gating/consumption before enabling scientific child.
 out={'schema_version':1,'kind':'JARVIS_GUARDED_BOUNDED_RESEARCH_V1','status':'DRY_RUN_PASS','execution_token':tok,'budget_candidates':budget,'child_process_started':False,'scientific_execution_enabled':False,'result_zone':'research-only','orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()}
 q=S/'guarded_bounded_research_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'guarded_bounded_research_v1.json')
 print('ALL PASS|GUARDED_BOUNDED_RESEARCH_V1|TOKEN_CONSUMED=YES|BUDGET='+str(budget)+'|CHILD_PROCESS=NO|DRY_RUN=YES');return 0
if __name__=='__main__':sys.exit(main())
