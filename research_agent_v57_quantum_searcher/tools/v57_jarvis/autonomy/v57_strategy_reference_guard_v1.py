#!/usr/bin/env python3
import re,sys,importlib.util
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy');G=A/'v57_strategy_pool_guard_v1.py'
def load():
 s=importlib.util.spec_from_file_location('poolguard',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def extract(q):
 m=re.search(r'(?i)(?:strategy(?:_id)?\s*[:=]?\s*)([0-9a-f]{64})',q);return m.group(1).lower() if m else None
def check(q):
 sid=extract(q)
 if not sid:return True,'NO_STRATEGY_REFERENCE',None
 ok,r=load().check(sid);return ok,r,sid
def main():
 q=' '.join(sys.argv[1:]);ok,r,sid=check(q);print(('PASS' if ok else 'STOP')+'|STRATEGY_REFERENCE_GUARD|'+r+'|'+str(sid));raise SystemExit(0 if ok else 3)
if __name__=='__main__':main()
