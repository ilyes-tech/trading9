#!/usr/bin/env python3
import json,sys,importlib.util
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
S=load('selector',A/'v57_verified_strategy_selector_v1.py');G=load('guard',A/'v57_strategy_pool_guard_v1.py')
def choose(symbol=None,timeframe=None,side=None):
 r=S.select(symbol,timeframe,side)
 if r.get('status')!='PASS':return r
 sid=r['selected']['strategy_id'];ok,reason=G.check(sid)
 if not ok:return {'status':'DENIED','reason':'POST_SELECTION_GUARD_'+reason,'selected':None,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False}
 r['post_selection_guard']='ACTIVE_VERIFIED';return r
def main():
 f={}
 for s in sys.argv[1:]:
  if '=' in s:k,v=s.split('=',1);f[k.lower()]=v
 print(json.dumps(choose(f.get('symbol'),f.get('timeframe'),f.get('side')),sort_keys=True))
if __name__=='__main__':main()
