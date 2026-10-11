import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
def _load(fn,name):
    p=HERE/fn
    if not p.is_file(): raise RuntimeError("MODULE_MISSING:"+fn)
    s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
REG=_load("v57_tool_registry_v3_3.py","j57v33reg")
LEDGER=_load("v57_experiment_ledger_v3_2.py","j57v32ledger")
DANGER=("real order","live order","demo order","order_send","private api","lance mt5","launch mt5","run mt5","start mt5","passe un ordre","place un ordre","envoie un ordre")
RESEARCH=("cherche","recherche","stratégie","strategie","candidate","candidat","backtest","hypothèse","hypothese","robuste")
def ask(text,evaluate=False,start=0,count=1,seed=574351):
    q=" ".join(str(text).strip().split()); low=q.lower()
    self_analysis=any(x in low for x in ("analyse ton propre","analyse ton fonctionnement","audite ton","perfectionner jarvis","améliorer jarvis","ameliorer jarvis","auto-analyse","self-analysis"))
    if self_analysis:
        try:
            r=REG.critic(q)
            return {"status":"COMPLETED","route":"SELF_ANALYSIS","result":r,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
        except Exception as e:
            return {"status":"FAILED","route":"SELF_ANALYSIS","reason":type(e).__name__+":"+str(e),"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    if evaluate is False and any(x in low for x in ("teste","tester","test ","backtest","évalue","evalue","évaluer","evaluer")): evaluate=True
    if not q: return {"status":"FAILED","reason":"EMPTY_REQUEST","orders_allowed":False,"mt5_launch_allowed":False}
    if any(x in low for x in DANGER): return {"status":"DENIED","reason":"MARKET_ACTION_DENIED","orders_allowed":False,"mt5_launch_allowed":False}
    if not any(x in low for x in RESEARCH): return {"status":"COMPLETED","route":"GENERAL","answer":"Mission générale reçue; aucune action externe exécutée.","promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    LEDGER.record("HYPOTHESIS",{"request":q,"seed":int(seed),"scope":"DEVELOPMENT_ONLY"})
    try:
        r=REG.run("SCIENTIST",{"hypothesis":q,"start":int(start),"count":int(count),"evaluate":bool(evaluate),"seed":int(seed)})
    except Exception as e:
        LEDGER.record("NEGATIVE_RESULT",{"request":q,"status":"FAILED","reason":type(e).__name__+":"+str(e),"seed":int(seed)})
        return {"status":"FAILED","route":"SCIENTIST","reason":type(e).__name__+":"+str(e),"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    LEDGER.record("EXPERIMENT",{"request":q,"status":r.get("status"),"evaluate":bool(evaluate),"start":int(start),"count":int(count),"seed":int(seed)})
    return {"status":"COMPLETED","route":"SCIENTIST","result":r,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
