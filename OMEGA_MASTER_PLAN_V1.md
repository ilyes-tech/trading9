# TRADINGAI OMEGA — PLAN DIRECTEUR MAJEUR V1.0
Date de reference: 2026-10-11. Statut: architecture approuvee, implementation a verifier. Ce document est la source de verite operationnelle du plan, et non une preuve de PASS.
## Mission
Construire au plus vite, sur VPS Ubuntu 4 CPU/8 Go, un laboratoire quantitatif JARVIS + Searcher autonome: hypothese falsifiable -> candidat -> backtest -> diagnostic -> amelioration controlee -> validation independante -> decision et memoire. Cible ambitieuse: PF >= 2.00 NET hors echantillon avec nombre de trades suffisant, risque/drawdown acceptable, couts realistes, robustesse et incertitude statistique; jamais de garantie de performance. AUCUN ORDRE REEL.
## Invariants non negociables
1. Progres = PASS prouve, pas nombre de scripts ni pourcentage invente.
2. Un seul objectif de construction actif: la prochaine capacite du chemin critique. Un candidat principal a la fois, mais abandonner les hypotheses refutees.
3. Reutiliser avant de reconstruire. Pas de migration, nouveau framework, dashboard, multi-agent, gros diagnostic ou campagne inutile sans preuve de besoin.
4. Avant modification: objectif, prerequis, chemin/compatibilite verifies, risque, rollback, test PASS/FAIL. Changements minimaux et reversibles; ne pas casser les freezes.
5. Les donnees, code, parametres, couts, version et decisions sont tracables; calculs deterministes, pas de fuite temporelle, pas d'optimisation sur holdout final.
6. Gardes scientifiques et permission d'execution independants du Searcher. Aucun ordre reel, aucun contournement des SAFE_STOP ou admissions DENIED.
7. Recherche a budget fini: CPU/RAM/temps/essais, stop explicite, apprentissage des echecs. Resultat negatif = resultat scientifique valable.
8. JARVIS integre au fur et a mesure, tests rapides apres chaque changement, tests profonds aux jalons; pas de services paralleles inutiles.
9. Les roles Chercheur, Planificateur, Executeur, Critique, Memoire sont des fonctions logiques, pas necessairement cinq agents IA.
10. Plan stable: modification de cap seulement avec preuve mesurable et tracee; details techniques adaptables apres audit.
## Architecture cible minimale
Direction humaine (objectifs et permissions) -> environnement de construction ChatGPT + Remote Desktop Commander + Git + tests -> JARVIS orchestrateur -> Data / Hypotheses / Experiments / Validation / Learning / Monitoring -> decision scientifique PASS, REJECT, REVISE, STOP. Un monolithe modulaire peut suffire.
## Phases et criteres de sortie
00 SECURISER: inventaire cible de l'existant, Git prive/local, sauvegarde testee, versions et rollback; PASS etat reproductible.
01 CONTRATS: schemas unifies donnees, strategies, experiences, couts, metriques, decisions; provenance, chronologie, separation temporelle, regles preenregistrees; PASS contrats testes.
02 DONNEES+BACKTEST: auditer et reutiliser moteur existant, integrite, determinisme, lookahead, frais/spread/slippage, tests unitaires/metamorphiques, references simples; PASS moteur de reference verifie.
03 PREMIERE EXPERIENCE: hypothese justifiee et admissible, candidat, backtest, diagnostic, rapport, decision (meme negative); PASS cycle reproductible.
04 AMELIORATION: faiblesse -> modification justifiee -> comparaison sur developpement -> conserver/rejeter; budget fini; PASS evolution controlee.
05 AUTONOMIE: JARVIS orchestre cycles autorises, memoire des echecs, anti-doublon, reprises, conditions d'arret; PASS plusieurs cycles de bout en bout sans intervention.
06 VALIDATION INDEPENDANTE: hors echantillon preserve, tests multiples, robustesse, sensibilite, regimes, incertitude, couts stresses, fidelite MT5; PASS acceptation/rejet independant. Garde-fous essentiels presents des phases 01-03.
07 MULTIMARCHE: etendre seulement aux marches avec donnees admissibles, comparabilite et mecanisme economique; PASS experiences comparables.
08 INTELLIGENCE AVANCEE: choix actif des experiences, critique adversariale, hypotheses equivalentes, multi-fidelite, cache, optimisations mesurees; PASS gain prouve vs baseline.
09 SIMULATION: paper trading, drift, monitoring, reprise panne, arret urgence, permissions separees; PASS simulation stable. Trading reel hors scope et necessite permission humaine explicite.
## Optimisations transversales
- Graphe de dependances et chemin critique, pas des phases rigides qui bloquent artificiellement.
- Deux voies: recherche/edits isoles et integration stable apres tests.
- Construire verticalement le plus petit cycle complet avant perfectionnement horizontal.
- Mesurer delai hypothese -> decision reproductible, interventions humaines, regression, experiences informatives par heure de calcul.
- Metriques multicriteres: PF net, activite, drawdown, robustesse, sensibilite, incertitude; PF ne suffit jamais.
- Preenregistrement des hypotheses, datasets et seuils; tests nuls, bootstrap blocs/purge/embargo si appropries, controle de multiple testing.
- Empreintes de provenance code/donnees/config, historique verifiable; memoires distinctes code/science/operations.
- Tests de panne et fail-closed: donnees manquantes, permission refusee, interruption -> STOP sans contournement.
- Git/pytest immediatement; Ruff et CI si benefice; DuckDB/Parquet selon volume; MLflow/Grafana et agents multiples seulement si besoin demontre.
- VPS principal nouveau; ancien VPS BACKUP ONLY; Termius secours, Remote Desktop Commander acces principal.
## Etat connu au 2026-10-11
VPS nouveau connecte. Runner systemd en SAFE_IDLE, SEARCH_EXECUTED=NO, ORDERS=NO. Multimarket 7, ADMITTED=0. Portes scientifiques SAFE_STOP_NO_NEW_HYPOTHESIS. Des moteurs hf_lab/replay.py, hf_lab/segmented_replay.py, V56 replay et tests existent. pytest present en .venv-research. Aucune racine .git detectee lors des inspections precedentes; a confirmer avant initialisation. Aucune premiere experience nouvelle complete prouvee. Ne pas annoncer d'avancement artificiel.
## Prochaine action
Audit cible en lecture seule des moteurs de backtest existants et des tests; choisir un moteur de reference et identifier les blocages exacts. Puis tests ciblés, sauvegarde/versionnement minimal, premier cycle scientifique autorise; si gates bloquent, ne pas les contourner.
## Protocole utilisateur
'continue' = executer sur le VPS la prochaine action sure du chemin critique, verifier PASS/FAIL, poursuivre autant que raisonnable dans le tour, rendre compte de l'etape/sous-etape, preuve, delta et blocage; demander uniquement permissions ou decisions indispensables. Pas de promesse de travail hors tour.
## Discipline d'amelioration
Ne pas rechercher la perfection theorique sans fin. Toute proposition nouvelle doit avoir preuve de gain, cout, risques, compatibilite, place dans le chemin critique. Si elle ne debloque rien, la differer. Ne jamais sacrifier securite et integrite scientifique pour la vitesse.
