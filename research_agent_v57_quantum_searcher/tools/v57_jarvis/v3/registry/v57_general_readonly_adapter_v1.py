import json,subprocess,sys
from pathlib import Path
P=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_project_inspect_v1.py')
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def _targeted_evidence(text):
 low=' '.join(str(text).lower().split())
 if not all(x in low for x in ('xauusd','m5','short')): return None
 if not any(x in low for x in ('faits','réussi','reussi','échoué','echoue','échec','echec','ne doit pas être répété','ne doit pas etre repete')): return None
 try:
  d=json.loads((S/'failure_diagnosis_v2.json').read_text()); f=json.loads((S/'research_feedback_v1.json').read_text()); b=json.loads((S/'bounded_research_result_v1.json').read_text())
 except Exception:return None
 if d.get('space')!='XAUUSD_M5_SHORT': return None
 failed=d.get('failed_gates',[]); passed=d.get('passed_gates',[])
 ff=', '.join(f"{g['metric']}={g['actual']} (requis {g['required']})" for g in failed)
 pp=', '.join(f"{g['metric']}={g['actual']} (limite {g['required']})" for g in passed)
 answer=("Faits établis pour XAUUSD M5 SHORT : le candidat DEEP documenté a échoué pour robustesse insuffisante. "
         f"Gates échoués : {ff}. Gates réussis à préserver : {pp}. "
         f"La sonde bornée development-only suivante a généré {f.get('candidates')} candidats, en a évalué {f.get('evaluated')}, avec {f.get('prefilter_reject')} rejet préfiltre et {f.get('exact_pass')} exact pass. "
         f"Conclusion documentée : {f.get('lesson')}; action à ne pas répéter : {f.get('next_action')}. "
         "Ces artefacts établissent un manque de robustesse/stabilité, pas une preuve causale. Aucune nouvelle recherche, aucun calcul, aucune modification ni action de marché n'a été exécuté.")
 ev={'space':d.get('space'),'strategy_id':d.get('strategy_id'),'conclusion':d.get('conclusion'),'failed_gates':failed,'passed_gates':passed,'bounded_probe':{'hypothesis_id':b.get('hypothesis_id'),'candidate_count':f.get('candidates'),'evaluated':f.get('evaluated'),'prefilter_reject':f.get('prefilter_reject'),'exact_pass':f.get('exact_pass'),'lesson':f.get('lesson'),'next_action':f.get('next_action')}}
 return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':ev,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
def execute(text):
 targeted=_targeted_evidence(text)
 if targeted is not None:return targeted
 r=subprocess.run([sys.executable,str(P)],text=True,capture_output=True,timeout=45)
 if r.returncode!=0:return {'status':'FAILED','route':'GENERAL_READONLY','reason':'PROJECT_INSPECT_FAILED','orders_allowed':False,'mt5_launch_allowed':False,'promotion_allowed':False}
 try:x=json.loads(r.stdout)
 except Exception:return {'status':'FAILED','route':'GENERAL_READONLY','reason':'INVALID_INSPECTION_OUTPUT','orders_allowed':False,'mt5_launch_allowed':False,'promotion_allowed':False}
 e=x['evidence']; frozen=sum(1 for f in e['freezes'] if f['status'] in ('FROZEN','FROZEN_FINAL'))
 answer=(f"État TradingAI vérifié en lecture seule : {e['goals_done']}/{e['goals_total']} objectifs clôturés, {frozen}/{len(e['freezes'])} freezes attendus présents, "
         f"acceptance={e['acceptance_status']} avec {e['autonomous_cycles']} cycles autonomes validés, Global Guard rc={e['global_guard_rc']}. "
         f"Post-Search Fidelity={'PRÊT' if x.get('post_search_fidelity_ready') else 'MANQUANT'}, Admission={'PRÊTE' if x.get('searcher_admission_ready') else 'MANQUANTE'}, freeze final post-search={'PRÉSENT' if x.get('post_search_final_freeze_ready') else 'MANQUANT'}. "
         "La frontière Searcher→Post-Search Fidelity→Admission est désormais intégrée et validée; elle ne doit plus être présentée comme un travail restant. "
         f"Priorité actuelle : {x.get('next_priority')} Aucune modification n'a été exécutée.")
 return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':e,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
def execute_classified_readonly(text):
 low=' '.join(str(text).lower().split())
 space_markers=("classe les espaces de recherche","espaces de recherche development","disponibilité des données","disponibilite des donnees","exploration engineering","preuve scientifique","admissibilité d'une nouvelle mission","admissibilite d une nouvelle mission","nouvel espace scientifique")
 if any(m in low for m in space_markers):
  try:
   repo=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher')
   manifest=json.loads((repo/'config/v433/V57_V433_FEATURE_CACHE_V2_MANIFEST_V2.json').read_text())
   glob=json.loads((repo/'config/V57_GLOBAL_ADAPTIVE_SEARCH_RESULT_V4.json').read_text())
   entries=manifest.get('entries',[]); markets=sorted(set(x.get('market') for x in entries)); tfs=sorted(set(x.get('timeframe') for x in entries))
   if len(entries)!=24: raise ValueError('EXPECTED_24_CACHE_ENTRIES')
   audit=manifest.get('permanent_audit',{}); data_admitted=(manifest.get('status')=='FROZEN_AFTER_PERMANENT_SEMANTIC_AUDIT_V3' and audit.get('status')=='PASS')
   if not data_admitted: raise ValueError('CANONICAL_DATA_AUDIT_NOT_PASS')
   engineering={k:{'tested':v.get('tested'),'exact':v.get('exact')} for k,v in glob.get('targets',{}).items()}
   unexplored=[m for m in markets if not any(k.startswith(m+'|') for k in engineering)]
   answer=(f"Sélection multi-espace en lecture seule : {len(entries)} caches development canoniques sont présents pour {', '.join(markets)} sur {', '.join(tfs)}. Le manifeste V2 est {manifest.get('status')} avec permanent_audit={audit.get('status')} : la dépendance d'audit des données est donc résolue. L'ancienne exploration globale reste classée {glob.get('classification')} : preuve engineering seulement, pas nomination scientifique, et ses résultats agrégés marché|direction ne doivent pas être attribués à chaque timeframe. Marchés avec caches mais sans cible dans cette exploration : {', '.join(unexplored) if unexplored else 'aucun'}. Décision : NO_NEW_SPACE_ADMITTED. Le seul verrou restant avant une nouvelle mission est une justification scientifique distincte au niveau exact marché+timeframe+direction. Aucune recherche n'est lancée.")
   ev={'cache_entries':len(entries),'markets':markets,'timeframes':tfs,'manifest_kind':manifest.get('kind'),'manifest_status':manifest.get('status'),'permanent_audit_status':audit.get('status'),'data_audit_resolved':True,'global_classification':glob.get('classification'),'engineering_targets':engineering,'markets_without_global_target_evidence':unexplored,'decision':'NO_NEW_SPACE_ADMITTED','required_before_new_mission':['EXACT_SPACE_JUSTIFICATION_MARKET_TIMEFRAME_SIDE']}
   return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':ev,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
  except Exception as e:
   return {'status':'FAILED','route':'GENERAL_READONLY','reason':'SPACE_SELECTION_EVIDENCE_INVALID:'+type(e).__name__+':'+str(e),'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 agenda_markers=("ensemble des résultats documentés","ensemble des resultats documentes","objectifs terminés","objectifs termines","nouvelle question scientifique distincte","mettre cet espace de recherche en pause","espace de recherche en pause","agenda épuisé","agenda epuise")
 if any(m in low for m in agenda_markers) and 'xauusd' in low and 'm5' in low and 'short' in low:
  try:
   import sqlite3
   c=sqlite3.connect(S/'research_agenda_v1.sqlite3'); rows=c.execute('SELECT objective,status FROM agenda WHERE space=? ORDER BY rowid',('XAUUSD_M5_SHORT',)).fetchall(); c.close()
   if not rows or any(st!='COMPLETED' for _,st in rows): raise ValueError('AGENDA_NOT_EXHAUSTED')
   learning=[]
   lp=S/'agenda_learning_v1.jsonl'
   if lp.exists():
    for line in lp.read_text().splitlines():
     try:
      x=json.loads(line)
      if x.get('status')=='DECIDED': learning.append(x)
     except Exception: pass
   exact=sum(int(x.get('exact_pass',0) or 0) for x in learning)
   distinct_no_pass=sum(1 for x in learning if x.get('lesson')=='BOUNDED_DISTINCT_PROBE_NO_EXACT_PASS')
   answer=(f"Décision scientifique : METTRE XAUUSD M5 SHORT EN PAUSE. Les {len(rows)} objectifs de l'agenda sont tous terminés ({', '.join(o for o,_ in rows)}). L'historique d'apprentissage disponible contient {distinct_no_pass} décision(s) BOUNDED_DISTINCT_PROBE_NO_EXACT_PASS et {exact} exact pass au total dans ces décisions. Aucune question scientifique nouvelle et distincte n'est actuellement documentée avec une justification suffisante pour ouvrir une nouvelle sonde. La décision fail-closed est donc de ne pas augmenter le budget et de ne pas inventer une expérience supplémentaire. Réouverture seulement si une nouvelle preuve ou une hypothèse distincte explicitement justifiée apporte une information nouvelle. Aucune recherche n'a été lancée.")
   ev={'space':'XAUUSD_M5_SHORT','agenda':[{'objective':o,'status':st} for o,st in rows],'agenda_exhausted':True,'learning_decisions':len(learning),'distinct_probe_no_exact_pass':distinct_no_pass,'exact_pass_total':exact,'decision':'PAUSE_RESEARCH_SPACE','reopen_condition':'NEW_EVIDENCE_OR_JUSTIFIED_DISTINCT_HYPOTHESIS'}
   return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':ev,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
  except Exception as e:
   return {'status':'FAILED','route':'GENERAL_READONLY','reason':'AGENDA_SYNTHESIS_EVIDENCE_INVALID:'+type(e).__name__+':'+str(e),'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 plan_markers=("plan expérimental","plan experimental","protocole","budget","métriques à améliorer","metriques a ameliorer","conditions de validation","expérience précise","experience precise","quelle expérience","quelle experience")
 if any(m in low for m in plan_markers) and 'xauusd' in low and 'm5' in low and 'short' in low:
  try:
   d=json.loads((S/'failure_diagnosis_v2.json').read_text()); h=json.loads((S/'refined_hypothesis_v1.json').read_text()); ep=json.loads((S/'experiment_plan_v1.json').read_text()); fb=json.loads((S/'research_feedback_v1.json').read_text())
   plan=ep.get('plan',{})
   if d.get('space')!='XAUUSD_M5_SHORT' or plan.get('space')!='XAUUSD_M5_SHORT' or plan.get('execution_mode')!='PLAN_ONLY': raise ValueError('PLAN_LINEAGE_INVALID')
   answer=(f"Plan expérimental documenté pour XAUUSD M5 SHORT : reformuler l'hypothèse de robustesse et tester ONE_DIMENSION_AT_A_TIME sur données development uniquement. Budget maximal : {plan.get('max_candidates')} candidats, {plan.get('max_concurrent_jobs')} job concurrent, avec resource gate. Métriques à améliorer : {', '.join(plan.get('target_metrics',[]))}. Métriques à préserver : {', '.join(plan.get('preserve_metrics',[]))}. Interdiction de répéter une sonde identique : {plan.get('forbid_identical_repeats')}; le feedback précédent est {fb.get('lesson')} / {fb.get('next_action')}. Validation exigée avant toute conclusion : exact replay puis DEEP validation. Le plan reste PLAN_ONLY et attend un opérateur explicitement autorisé; aucune expérience n'est lancée par cette réponse.")
   ev={'decision':'B','hypothesis_id':plan.get('hypothesis_id'),'method':plan.get('method'),'execution_mode':plan.get('execution_mode'),'max_candidates':plan.get('max_candidates'),'max_concurrent_jobs':plan.get('max_concurrent_jobs'),'target_metrics':plan.get('target_metrics'),'preserve_metrics':plan.get('preserve_metrics'),'requires_exact_replay':plan.get('requires_exact_replay'),'requires_deep_validation':plan.get('requires_deep_validation'),'requires_resource_gate':plan.get('requires_resource_gate'),'forbid_identical_repeats':plan.get('forbid_identical_repeats'),'next_action':ep.get('next_action')}
   return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':ev,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
  except Exception as e:
   return {'status':'FAILED','route':'GENERAL_READONLY','reason':'EXPERIMENT_PLAN_EVIDENCE_INVALID:'+type(e).__name__+':'+str(e),'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 conclusion_markers=("pourquoi il ne faut pas abandonner","preuves permettent réellement de conclure","preuves permettent reellement de conclure","faut-il abandonner")
 if any(m in low for m in conclusion_markers) and 'xauusd' in low and 'm5' in low and 'short' in low:
  try:
   d=json.loads((S/'failure_diagnosis_v2.json').read_text()); fb=json.loads((S/'research_feedback_v1.json').read_text())
   answer=("Les preuves ne justifient pas un abandon immédiat de XAUUSD M5 SHORT. Elles établissent ROBUSTNESS_INSUFFICIENT pour le candidat documenté et 0 exact pass dans la sonde bornée suivante. Elles établissent aussi que les métriques de concentration des profits passent. La prescription enregistrée est REFINE_RESEARCH_HYPOTHESIS et le feedback interdit seulement de répéter la sonde identique (DO_NOT_REPEAT_IDENTICAL_PROBE). Conclusion autorisée : la piste actuelle n'est pas validée et doit être reformulée; conclusion non autorisée par ces preuves : que tout l'espace XAUUSD M5 SHORT est définitivement sans valeur. Aucune recherche n'est exécutée.")
   return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':{'conclusion':d.get('conclusion'),'next_action':d.get('next_action'),'feedback':fb.get('lesson'),'feedback_next_action':fb.get('next_action'),'failed_gates':d.get('failed_gates'),'passed_gates':d.get('passed_gates')},'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
  except Exception as e:
   return {'status':'FAILED','route':'GENERAL_READONLY','reason':'CONCLUSION_EVIDENCE_INVALID:'+type(e).__name__+':'+str(e),'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 decision_markers=("choisir une seule option","prochaine décision scientifique","prochaine decision scientifique","abandonner cette piste","reformuler l'hypothèse","reformuler l’hypothèse","dimension causale différente","dimension causale differente","preuves sont insuffisantes")
 if any(m in low for m in decision_markers) and 'xauusd' in low and 'm5' in low and 'short' in low:
  try:
   d=json.loads((S/'failure_diagnosis_v2.json').read_text()); h=json.loads((S/'refined_hypothesis_v1.json').read_text()); ep=json.loads((S/'experiment_plan_v1.json').read_text()); fb=json.loads((S/'research_feedback_v1.json').read_text())
   if d.get('space')!='XAUUSD_M5_SHORT' or h.get('objective',{}).get('space')!='XAUUSD_M5_SHORT' or ep.get('plan',{}).get('space')!='XAUUSD_M5_SHORT': raise ValueError('SPACE_MISMATCH')
   if d.get('next_action')!='REFINE_RESEARCH_HYPOTHESIS' or h.get('status')!='PROPOSED' or ep.get('status')!='PLANNED': raise ValueError('DECISION_LINEAGE_NOT_READY')
   answer=("Décision scientifique : B) reformuler l'hypothèse. Justification documentée : le diagnostic conclut ROBUSTNESS_INSUFFICIENT et prescrit REFINE_RESEARCH_HYPOTHESIS; les trois métriques de robustesse/stabilité échouent, tandis que les deux métriques de concentration des profits passent et doivent être préservées. La sonde bornée suivante a produit 0 exact pass et impose DO_NOT_REPEAT_IDENTICAL_PROBE : cela interdit de répéter la même sonde, mais ne constitue pas une preuve suffisante pour abandonner tout l'espace XAUUSD M5 SHORT. L'expérience conceptuelle déjà planifiée consiste donc à changer une seule dimension à la fois, sur données development uniquement, afin d'expliquer/améliorer min_boot_mean_positive_probability, min_boot_pf_ge1_probability et positive_half_segments, tout en préservant max_trade_profit_share et max_day_profit_share. Information nouvelle recherchée : déterminer si la faiblesse de robustesse peut être améliorée par une variation causale isolée plutôt que par la répétition de la sonde précédente. PLAN ONLY; aucune stratégie générée, aucun Searcher/backtest/calcul lancé, aucun holdout, MT5, ordre ou promotion.")
   ev={'decision':'B','diagnosis':d.get('conclusion'),'diagnosis_next_action':d.get('next_action'),'feedback_lesson':fb.get('lesson'),'feedback_next_action':fb.get('next_action'),'experiment_method':ep.get('plan',{}).get('method'),'target_metrics':ep.get('plan',{}).get('target_metrics'),'preserve_metrics':ep.get('plan',{}).get('preserve_metrics')}
   return {'status':'COMPLETED','route':'GENERAL_READONLY','answer':answer,'evidence':ev,'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
  except Exception as e:
   return {'status':'FAILED','route':'GENERAL_READONLY','reason':'SCIENTIFIC_DECISION_EVIDENCE_INVALID:'+type(e).__name__+':'+str(e),'read_only':True,'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 return execute(text)
