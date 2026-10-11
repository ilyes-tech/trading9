#!/usr/bin/env python3
import json,tempfile,importlib.util
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=load('guard',A/'v57_strategy_pool_guard_v1.py');S=load('selector',A/'v57_verified_strategy_selector_v1.py')
def main():
 r=S.select('XAUUSD',None,'SHORT');assert r['status']=='PASS';sid=r['selected']['strategy_id'];orig=G.POOL
 with tempfile.TemporaryDirectory(prefix='v57_pool_revoke_') as td:
  p=Path(td)/'pool.json';x=json.loads(orig.read_text());x['active']=[z for z in x['active'] if z['strategy_id']!=sid];x['active_count']=len(x['active']);x['revoked'].append({'strategy_id':sid,'reason':'ISOLATED_SELFTEST_REVOCATION'});x['revoked_count']=len(x['revoked']);x.pop('pool_sha256',None);import hashlib;x['pool_sha256']=hashlib.sha256(G.canon(x).encode()).hexdigest();p.write_text(json.dumps(x));G.POOL=p
  try:ok,reason=G.check(sid)
  finally:G.POOL=orig
 assert not ok and reason=='STRATEGY_NOT_ACTIVE';ok2,reason2=G.check(sid);assert ok2 and reason2=='ACTIVE_VERIFIED'
 print('PASS|REVOCATION_E2E_SELFTEST|ISOLATED=STRATEGY_NOT_ACTIVE|PRODUCTION=ACTIVE_VERIFIED|SID='+sid)
if __name__=='__main__':main()
