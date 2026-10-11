#!/usr/bin/env python3
import importlib.util,json
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
RT=load('router',A/'v57_capability_router_v1.py')
def main():
 r=RT.run('INTENTIONALLY_NOT_ALLOWLISTED')
 ok=r.get('status')=='DENIED' and r.get('reason')=='NOT_ALLOWLISTED'
 out={'kind':'JARVIS_CONTROLLER_FAILURE_TEST_V1','status':'PASS' if ok else 'FAIL','controlled_failure':r,'production_state_modified':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'mutation_allowed':False}
 print(json.dumps(out,sort_keys=True));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
