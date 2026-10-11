#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher'); STATE=R/'work/autopilot_v433/cumulative_state.json'; PROOFS=R/'work/deployment_fidelity_v1/proofs'
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def verify(sid):
 try: p=json.loads((PROOFS/(sid+'.json')).read_text()); x=json.loads(STATE.read_text()); s=x['archive']['exact_backlog'][sid]['strategy']
 except Exception: return False,'MISSING_OR_UNREADABLE'
 h=p.get('proof_sha256'); q=dict(p); q.pop('proof_sha256',None)
 if hashlib.sha256(canon(q).encode()).hexdigest()!=h:return False,'PROOF_HASH_MISMATCH'
 if hashlib.sha256(canon(s).encode()).hexdigest()!=p.get('strategy_sha256'):return False,'STRATEGY_HASH_MISMATCH'
 if p.get('strategy_id')!=sid or not p.get('promotion_allowed'):return False,'NOT_PROMOTABLE'
 v=p.get('verdict',{}); integ=v.get('research_integrity',{})
 if v.get('conclusion')!='DEPLOYMENT_VERIFIED' or integ.get('holdout_read') or integ.get('orders_allowed') or integ.get('september_2026_data_accessed'):return False,'INTEGRITY_OR_VERDICT_FAIL'
 return True,'VERIFIED'
def main():
 sid=sys.argv[1] if len(sys.argv)>1 else ''; ok,reason=verify(sid); print(('PASS' if ok else 'STOP')+'|FIDELITY_VERIFY|'+reason+'|'+sid); raise SystemExit(0 if ok else 3)
if __name__=='__main__':main()
