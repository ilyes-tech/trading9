#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher');POOL=R/'work/v57_jarvis/dynamic_verified_pool_v1.json'
def select(symbol=None,timeframe=None,side=None):
 x=json.loads(POOL.read_text()); rows=x.get('active',[])
 if symbol: rows=[z for z in rows if z['market'].get('symbol')==symbol]
 if timeframe: rows=[z for z in rows if z['market'].get('timeframe')==timeframe]
 if side: rows=[z for z in rows if z.get('side')==side]
 rows=sorted(rows,key=lambda z:(-(z.get('fixed_min_stress_pf') or 0),z['strategy_id']))
 if not rows:return {'status':'DENIED','reason':'NO_ACTIVE_VERIFIED_MATCH','selected':None,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False}
 z=rows[0];return {'status':'PASS','reason':'DETERMINISTIC_DEV_METRIC_SELECTION','selected':z,'candidate_count':len(rows),'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False}
def main():
 a=sys.argv[1:];f={};
 for s in a:
  if '=' in s:k,v=s.split('=',1);f[k.lower()]=v
 r=select(f.get('symbol'),f.get('timeframe'),f.get('side'));print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r.get('status')=='PASS' else 3)
if __name__=='__main__':main()
