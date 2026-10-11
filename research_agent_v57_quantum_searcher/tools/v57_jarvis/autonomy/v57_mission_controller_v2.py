#!/usr/bin/env python3
import importlib.util,subprocess,json,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';PY=R/'.venv-research/bin/python'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
BR=load('bridge3',A/'v57_general_mission_bridge_v3.py');FC=load('fc',A/'v57_failure_classifier_v1.py')
def main():
 q=' '.join(sys.argv[1:]).strip()
 if not q: print('STOP|FAIL|MISSION_CONTROLLER_V2|EMPTY');raise SystemExit(2)
 mission=BR.execute(q);cl=FC.classify(mission)
 if cl=='CONTROLLED_REJECTION':print('STOP|DENIED|MISSION_CONTROLLER_V2|CONTROLLED_REJECTION');raise SystemExit(3)
 if cl!='SUCCESS':print('STOP|FAIL|MISSION_CONTROLLER_V2|MISSION_FAILURE');raise SystemExit(1)
 learn=subprocess.run([str(PY),str(A/'v57_mission_learning_cycle_v1.py')],cwd=R,text=True,capture_output=True,timeout=120)
 if learn.returncode:print('STOP|FAIL|MISSION_CONTROLLER_V2|LEARNING');raise SystemExit(1)
 print(json.dumps({'status':'PASS','kind':'JARVIS_MISSION_CONTROLLER_V2','mission_id':mission['mission_id'],'mission_kind':mission['mission_kind'],'classification':cl,'learning':'PASS','orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'mutation_allowed':False},sort_keys=True))
if __name__=='__main__':main()
