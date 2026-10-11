#!/usr/bin/env python3
import hashlib,json,pathlib,stat,sys
R=pathlib.Path(__file__).resolve().parents[3];A=pathlib.Path(__file__).resolve().parent;S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def fail(x):print('STOP|FAIL|GLOBAL_AUTONOMY_FREEZE_GUARD|'+x);return 3
def verify_manifest(name,count):
 p=A/name
 if not p.exists():raise ValueError(name+'_MISSING')
 m=load(p)
 if m.get('status')!='FROZEN' or len(m.get('components') or {})!=count:raise ValueError(name+'_INVALID')
 if p.stat().st_mode & 0o222:raise ValueError(name+'_WRITABLE')
 for rel,h in m['components'].items():
  q=R/rel
  if not q.exists() or H(q)!=h or q.stat().st_mode & 0o222:raise ValueError('COMPONENT_INVALID:'+rel)
 return m

def main():
 try:
  p2=verify_manifest('PHASE2_RESEARCH_SAFETY_FREEZE_V1.json',5);sup=verify_manifest('PHASE2_SUPERVISOR_FREEZE_V1.json',3)
  if H(A/'PHASE2_RESEARCH_SAFETY_FREEZE_V1.json')!=sup.get('base_phase2_freeze_sha256'):raise ValueError('CROSS_HASH_INVALID')
  g=load(S/'search_execution_gate_v1.json');l1=load(S/'search_execution_ledger_v1.json');l2=load(S/'phase2_scientific_execution_ledger_v1.json')
  if g.get('ready') is not False or g.get('execution_token') is not None or g.get('budget_candidates')!=0:raise ValueError('GATE_NOT_NEUTRAL')
  if l1.get('consumed_tokens') or l2.get('completed_tokens'):raise ValueError('LEDGERS_NOT_NEUTRAL')
  for m in (p2,sup):
   inv=m.get('invariants') or {}
   for k in ('pool_mutation_allowed','auto_promotion_allowed','orders_allowed','mt5_allowed','holdout_allowed'):
    if inv.get(k) is not False:raise ValueError('INVARIANT_OPEN:'+k)
  if p2['invariants'].get('bounded_candidate_budget_max')!=4 or sup['invariants'].get('candidate_budget_max')!=4:raise ValueError('BUDGET_CAP_INVALID')
  import subprocess
  q=subprocess.run([sys.executable,str(A/'v57_core_freeze_guard_v1.py')],capture_output=True,text=True)
  if q.returncode!=0:raise ValueError('CORE_FREEZE_INVALID')
  print('ALL PASS|GLOBAL_AUTONOMY_FREEZE_GUARD|CORE=PASS|PHASE2=PASS|SUPERVISOR=PASS|STATE=NEUTRAL|BUDGET_MAX=4|PROMOTION=NO|ORDERS=NO');return 0
 except Exception as e:return fail(str(e))
if __name__=='__main__':sys.exit(main())
