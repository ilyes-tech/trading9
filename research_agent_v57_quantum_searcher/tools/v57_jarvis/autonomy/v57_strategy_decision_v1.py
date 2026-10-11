#!/usr/bin/env python3
import json,hashlib,datetime,importlib.util,sys,fcntl
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy');LOG=Path('/home/trading/.local/state/tradingai/jarvis-autonomous/strategy_decisions_v1.jsonl')
def load():
 s=importlib.util.spec_from_file_location('selectionbridge',A/'v57_strategy_selection_bridge_v1.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def verify_chain(path=None):
 path=LOG if path is None else Path(path)
 if not path.exists():return True,'0'*64
 try:a=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
 except Exception:return False,None
 prev='0'*64
 for e in a:
  h=e.get('event_sha256');q=dict(e);q.pop('event_sha256',None)
  if e.get('prev_sha256')!=prev or hashlib.sha256(canon(q).encode()).hexdigest()!=h:return False,None
  prev=h
 return True,prev
def decide(symbol=None,timeframe=None,side=None):
 LOG.parent.mkdir(parents=True,exist_ok=True);lock=LOG.with_suffix(LOG.suffix+'.lock')
 with open(lock,'a+') as lf:
  fcntl.flock(lf,fcntl.LOCK_EX)
  ok,prev=verify_chain()
  if not ok:return {'status':'DENIED','reason':'AUDIT_CHAIN_INVALID','selected':None,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False},None
  r=load().choose(symbol,timeframe,side);e={'ts':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'JARVIS_STRATEGY_DECISION_V1','filters':{'symbol':symbol,'timeframe':timeframe,'side':side},'status':r['status'],'reason':r['reason'],'strategy_id':(r.get('selected') or {}).get('strategy_id'),'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'prev_sha256':prev}
  e['event_sha256']=hashlib.sha256(canon(e).encode()).hexdigest()
  with open(LOG,'a') as out:out.write(json.dumps(e,sort_keys=True)+'\n');out.flush();__import__('os').fsync(out.fileno())
  return r,e
def main():
 f={}
 for s in sys.argv[1:]:
  if '=' in s:k,v=s.split('=',1);f[k.lower()]=v
 r,e=decide(f.get('symbol'),f.get('timeframe'),f.get('side'));print(json.dumps({'decision':e,'selection':r},sort_keys=True));raise SystemExit(0 if r['status']=='PASS' else 3)
if __name__=='__main__':main()
