#!/usr/bin/env python3
import json,tempfile,importlib.util
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('mission',A/'v57_general_mission_bridge_v3.py');D=M.SD
def main():
 orig=D.LOG;prod=orig.read_bytes()
 with tempfile.TemporaryDirectory(prefix='v57_audit_e2e_') as td:
  p=Path(td)/'audit.jsonl';a=[json.loads(x) for x in orig.read_text().splitlines() if x.strip()];assert a;a[0]['reason']='TAMPERED';p.write_text('\n'.join(json.dumps(x,sort_keys=True) for x in a)+'\n');D.LOG=p
  try:r=M.execute('analyse searcher candidate')
  finally:D.LOG=orig
 assert r['status']=='FAILED' and r['reason']=='AUTONOMOUS_STRATEGY_SELECTION_DENIED';assert isinstance(r['decision'],dict) and r['decision'].get('audit') is None and r['decision'].get('selection',{}).get('status')=='DENIED' and r['decision']['selection'].get('reason')=='AUDIT_CHAIN_INVALID';assert r['execution'] is False and r['orders_allowed'] is False and r['mt5_allowed'] is False;assert orig.read_bytes()==prod and D.verify_chain()[0]
 print('PASS|AUDIT_FAILCLOSED_E2E|TAMPER=DENIED|PRODUCTION_UNCHANGED=TRUE|PRODUCTION_CHAIN=VALID')
if __name__=='__main__':main()
