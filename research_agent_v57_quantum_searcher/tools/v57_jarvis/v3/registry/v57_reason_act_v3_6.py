import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
def _load(fn,name):
    p=HERE/fn
    if not p.is_file(): raise RuntimeError("MODULE_MISSING:"+fn)
    s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
REG=_load("v57_tool_registry_v3_6.py","j57v36reg")
LEDGER=_load("v57_experiment_ledger_v3_2.py","j57v32ledger")
GENERAL=_load("v57_mission_execution_router_v1.py","j57missionexecv1")
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
    project_intent=any(x in low for x in ("état actuel du projet","etat actuel du projet","état du projet","etat du projet","état actuel de tradingai","etat actuel de tradingai","état actuel documenté","etat actuel documente","point sur l état","point sur l’état","point sur l etat","point sur le projet","où en sommes","ou en sommes","où en est","ou en est","ce qu il reste à faire","ce qu’il reste à faire","ce qu il reste a faire","ce qu’il reste a faire","reste à faire","reste a faire","prochaine priorité","prochaine priorite","priorité du projet","priorite du projet","plan d’action","plan d action","bilan du projet","bilan tradingai","faits établis","faits etablis","causes d'échec","causes d’échec","causes d echec","ce qui a réussi","ce qui a reussi","ce qui a échoué","ce qui a echoue"))
    readonly_constraint=any(x in low for x in ("analyse en lecture seule","lecture seule","n'effectue aucune recherche","n’effectue aucune recherche","ne lance aucune recherche","ne lance aucun backtest","aucun calcul","aucune modification","n'exécute aucune action","n’exécute aucune action","plan only"))
    explicit_research_action=any(x in low for x in ("cherche une stratégie","cherche une strategie","recherche une stratégie","recherche une strategie","génère une stratégie","genere une strategie","backtest","teste une stratégie","teste une strategie","évalue une stratégie","evalue une strategie"))
    if readonly_constraint or (project_intent and not explicit_research_action):
        try:return GENERAL.route(q,classified_readonly=True)
        except Exception as e:return {"status":"FAILED","route":"GENERAL_READONLY","reason":type(e).__name__+":"+str(e),"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    if not any(x in low for x in RESEARCH):
        try:return GENERAL.route(q)
        except Exception as e:return {"status":"FAILED","route":"GENERAL_READONLY","reason":type(e).__name__+":"+str(e),"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    LEDGER.record("HYPOTHESIS",{"request":q,"seed":int(seed),"scope":"DEVELOPMENT_ONLY"})
    try:
        r=REG.run("SCIENTIST",{"hypothesis":q,"start":int(start),"count":int(count),"evaluate":bool(evaluate),"seed":int(seed)})
    except Exception as e:
        LEDGER.record("NEGATIVE_RESULT",{"request":q,"status":"FAILED","reason":type(e).__name__+":"+str(e),"seed":int(seed)})
        return {"status":"FAILED","route":"SCIENTIST","reason":type(e).__name__+":"+str(e),"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
    LEDGER.record("EXPERIMENT",{"request":q,"status":r.get("status"),"evaluate":bool(evaluate),"start":int(start),"count":int(count),"seed":int(seed)})
    return {"status":"COMPLETED","route":"SCIENTIST","result":r,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False}
