import importlib.util
from pathlib import Path
ENGINE="V57_JARVIS_SCIENTIST_V3"
ROOT=Path(__file__).resolve().parents[2]
V2=ROOT/"registry/v57_scientist_v1.py"
def _load():
    s=importlib.util.spec_from_file_location("j57_scientist_v1_ro",V2)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def experiment(hypothesis,start=0,count=1,evaluate=False):
    if not str(hypothesis).strip(): raise ValueError("EMPTY_HYPOTHESIS")
    if start < 0 or count < 1: raise ValueError("BAD_RANGE")
    if count > 32: raise ValueError("COUNT_LIMIT")
    r=_load().hypothesis(str(hypothesis),int(start),int(count),bool(evaluate))
    return {"engine":ENGINE,"status":"COMPLETED","result":r,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False,"mutation_allowed":False}
