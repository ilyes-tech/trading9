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
## Etat verifie au 2026-10-16 (remplace le snapshot du 2026-10-11)
VPS principal et runner systemd actifs; depot Git local versionne; moteur historique hf_lab/replay.py et segmented_replay.py present et teste. Les tests hf_lab/tests ont passe (158 tests et 75 sous-tests au dernier jalon). L'alignement horloge entre BTC-ETH est teste et distingue 79249 decisions causales du sous-ensemble de 79231 fenetres a label complet; aucun signal, rendement ou backtest sur les donnees reelles n'a ete calcule. Les portes autonomes demeurent DENIED: autorisation de recherche=false, max_candidates=0, nouveau candidat admis=false. Ne pas interpreter la disponibilite technique du moteur comme une admission scientifique.
Etape 03 non close: les 12 candidats Coinbase M1 Q4 2025 (6 BTCUSD, 6 ETHUSD) ont des resultats d'entrainement negatifs; triage prouve par OMEGA_STAGE03_HISTORICAL_TRAIN_ONLY_TRIAGE_V1.json, sans lecture de validation ou holdout. JARVIS memorise 60 observations dont ces 12 rejets. Aucun nouveau backtest autorise, aucune hypothese validee. Ecart de taille manifeste/CSV explique par reexport des timestamps UTC (+00:00 vers Z), corrobore par le journal post-reparation et sans modification des fichiers originaux. Les 158536 lignes des deux prefixes entrainement sont exactement egales a la base locale de telechargement; 16 bougies echantillonnees concordent avec Coinbase. Ces controles techniques ne prouvent ni attestation externe complete, ni autorisation scientifique. Aucune zone de validation ou holdout n'a ete lue par l'audit.
Le dossier liquide BTCUSD_PERP peut rester en revue externe sans etre une dependance artificielle pour TOUTES les futures experiences de developpement; sa revue scientifique et ses preuves prospectives restent manquantes. Les autorisations de recherche, validation finale, MT5 et ordres restent distinctes et fermees. Aucune performance PF>=2 demontree.
## Prochaine action
STOP ETAPE 03 -- deux dependances non resolubles par des tests synthetiques supplementaires. (A) Aucune revue methodologique independante reelle BTC-ETH n'a ete rendue; dossier v2 controle dans OMEGA_STAGE03_BTC_ETH_REVIEW_HANDOFF_V1.md, a transmettre a un evaluateur externe. (B) v57_search_authorization_gate_v1.py contient volontairement un refus inconditionnel INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE: meme une revue positive ne vaut pas autorisation automatique. Toute permission experimentale BTC-ETH retrospective train-only doit faire l'objet d'une voie scientifiquement et independamment revue, bornees a une hypothese, dataset prefix train, couts verificables et budget fini, avec tests fail-closed, sans ouvrir Searcher/holdout/MT5/ordres. Tant que ces deux dependances manquent, ne pas continuer a ajouter des modules/diagnostics ou refaire des backtests; conserver SAFE_IDLE et conserver le dossier v2 inchange. Etape 03 ne peut etre dite PASS que lorsqu'un vrai cycle autorise, reproductible, a ete execute et une decision tracee (meme REJECT) etablie.
## Protocole utilisateur
'continue' = executer sur le VPS la prochaine action sure du chemin critique, verifier PASS/FAIL, poursuivre autant que raisonnable dans le tour, rendre compte de l'etape/sous-etape, preuve, delta et blocage; demander uniquement permissions ou decisions indispensables. Pas de promesse de travail hors tour.
## Discipline d'amelioration
Ne pas rechercher la perfection theorique sans fin. Toute proposition nouvelle doit avoir preuve de gain, cout, risques, compatibilite, place dans le chemin critique. Si elle ne debloque rien, la differer. Ne jamais sacrifier securite et integrite scientifique pour la vitesse.
