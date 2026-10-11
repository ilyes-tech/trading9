#!/usr/bin/env python3
import json,hashlib,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');POOL=R/'work/v57_jarvis/dynamic_verified_pool_v1.json'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def check(sid):
 try:x=json.loads(POOL.read_text())
 except Exception:return False,'POOL_MISSING_OR_UNREADABLE'
 h=x.get('pool_sha256');q=dict(x);q.pop('pool_sha256',None)
 if hashlib.sha256(canon(q).encode()).hexdigest()!=h:return False,'POOL_HASH_MISMATCH'
 if x.get('execution_allowed') or x.get('orders_allowed') or x.get('mt5_allowed') or x.get('holdout_allowed'):return False,'POOL_SAFETY_FAIL'
 z=next((a for a in x.get('active',[]) if a.get('strategy_id')==sid),None)
 if not z:return False,'STRATEGY_NOT_ACTIVE'
 if z.get('execution_allowed'):return False,'STRATEGY_EXECUTION_FLAG_FAIL'
 return True,'ACTIVE_VERIFIED'
def main():
 sid=sys.argv[1] if len(sys.argv)>1 else '';ok,r=check(sid);print(('PASS' if ok else 'STOP')+'|STRATEGY_POOL_GUARD|'+r+'|'+sid);raise SystemExit(0 if ok else 3)
if __name__=='__main__':main()
