import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
def _load(fn,name):
    p=HERE/fn; s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
REG=_load("v57_tool_registry_v3.py","j57v3reg")
LEDGER=_load("v57_experiment_ledger_v3.py","j57v3ledger")
DANGER=("real order","live order","demo order","order_send","private api","lance mt5","launch mt5","run mt5","start mt5","passe un ordre","place un ordre","envoie un ordre")
def ask(text,evaluate=False,start=0,count=1):
    q=" ".join(str(text).strip().split()); low=q.lower()
    if not q: return {"status":"FAILED","reason":"EMPTY_REQUEST"}
    if any(x in low for x in DANGER): return {"status":"DENIED","reason":"MARKET_ACTION_DENIED","orders_allowed":False,"mt5_launch_allowed":False}
    research=any(x in low for x in ("cherche","recherche","stratégie","strategie","candidate","candidat","backtest","hypothèse","hypothese","robuste"))
    if research:
        LEDGER.record("HYPOTHESIS",{"request":q})
        r=REG.run("SCIENTIST",{"hypothesis":q,"start":start,"count":count,"evaluate":evaluate})
        LEDGER.record("EXPERIMENT",{"request":q,"status":r.get("status"),"evaluate":bool(evaluate),"start":start,"count":count})
        return {"status":"COMPLETED","route":"SCIENTIST","result":r,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    return {"status":"COMPLETED","route":"GENERAL","answer":"JARVIS V3 opérationnel. Mission générale reçue; aucune action externe exécutée.","promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
