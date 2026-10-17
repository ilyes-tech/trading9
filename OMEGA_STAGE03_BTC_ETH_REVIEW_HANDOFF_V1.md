# OMEGA Stage03 BTC–ETH — dossier de revue indépendante (non approuvé)

Le dossier signé n’existe pas ; ceci est un envoi de preuves et de questions **sans autorisation**.

- Archive sur le VPS : `/home/trading/.local/state/tradingai/jarvis-autonomous/stage03_btc_eth_independent_review_v2.zip`
- SHA-256 archive : `d1a9e8e20f3d960a6f91c3fc289f17aad4337bcd19113a5dec82922e846c2e6a`
- Contenu : 9 fichiers sources existants, README et manifeste de hachages; module et tests mis à jour (18 tests synthétiques), contrôlés un par un.
- Pas de données brutes prix, données de validation, holdout, identifiants ni clés privées dans l’archive.
- Revue requise : originalité/antériorité, causalité, frais réels, possibilité du short ETH, qualité/provenance, portée rétrospective, autorisation indépendante.
- Aucun backtest nouveau ni ordre. La porte Searcher reste DENIED.

### Vérification instrument / exécution publique (sources consultées le 2026-10-17)

Ce complément est une QUESTION DE REVUE, pas une modification du protocole fige, un backtest, un avis independant ou une admission.

- Les 2 séries M1 du protocole portent sur **Coinbase Exchange SPOT BTC-USD / ETH-USD, 2025-Q4** (voir OMEGA_STAGE03_BTC_ETH_LEAD_LAG_REVIEW_ONLY_V1.json). Une vente a decouvert d'ETH ne peut pas etre presumee executable simplement parce que les cours spot ETH-USD existent. Distinguer signal directionnel, instrument reel tradable et compte/permissions.
- Coinbase a annonce le **9 mars 2026** le deploiement progressif de contrats futures pour les utilisateurs eligibles en France, dont certains contrats ETH. Ceci est **posterieur a 2025-Q4** et NE prouve pas que le contrat etait disponible a cette date, ni l'eligibilite de l'utilisateur, ni des executions/frais au prix spot.
  Source officielle: https://www.coinbase.com/en-fr/blog/futures-contracts-europe
- Coinbase indique un **onboarding et une evaluation d'adequation** pour les utilisateurs EEE; acces eventuellement refuse. La realite du produit ETH, du tick/minimum notionnel, de la marge et des commissions doit etre confirmee pour le lieu/mode d'execution choisi. Aucune capacite utilisateur n'est attestee.
  Source officielle: https://help.coinbase.com/en/coinbase/derivatives/us-derivatives-intro
- Pour les **perpetuals mondiaux** Coinbase International, la plateforme annonce une integration Deribit terminee le **1er octobre 2026**. Ce fait souligne le risque de differences d'instruments et d'API entre historique et execution actuelle; il **ne demontre pas** que l'offre future Europe/MiFID est identique aux perpetuals mondiaux concernes par cette migration.
  Source officielle: https://help.coinbase.com/en/international-exchange/deribit/what-you-need-to-know
- Le dossier de protocole signale deja que **12 bps aller-retour** etaient une hypothese d'ingenierie; son examen des baremes publics Coinbase Exchange SPOT donne une indication de **120 bps aller-retour taker de bas volume** (hors slippage/spread), *pas* une commission personnelle certifiee, ni un prix pour les futures ou MT5. Ne JAMAIS importer un bareme spot dans un modele futures/MT5 sans validation du produit, du financement, du contrat, du courtier et de la date.
  Provenance: OMEGA_STAGE03_BTC_ETH_LEAD_LAG_REVIEW_ONLY_V1.json, champ real_venue_fee_preflight, source https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees

**Points de decision a demander a l'evaluateur :** (a) hypothese purement predictive ou strategie short ETH effectivement executable ? (b) quel instrument, quelle venue et quelles donnees historiques d'execution correspondent aux signaux spot 2025-Q4, y compris funding et spread ? (c) faut-il REJECT/REVISE faute de preuve de fidelite et d'executabilite avant toute experimentation ? Aucune conversion implicite d'un signal spot en profit futures/MT5.

**Réponse externe attendue** : revue explicite avec corrections ou rejet motivé. Une revue favorable ne constitue pas à elle seule une autorisation d’expérience et ne modifie aucun garde-fou.

**Deux dependances distinctes et non satisfaites :**
1. Un evaluateur externe reel doit rendre un avis methodologique explicite sur ce protocole BTC-ETH; aucun avis signe ni autorite de revue BTC-ETH n'est disponible. Une publication sur le sujet n'est pas une evaluation de cette implementation.
2. La porte actuelle `v57_search_authorization_gate_v1.py` ajoute systematiquement `INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE`; il n'existe pas de voie BTC-ETH autonome deja approuvee pour signer et limiter UNE experience retrospective train-only. Meme un avis externe positif ne debloque pas automatiquement cette porte. Une autorite distincte doit approuver une voie de permission scientifique bornee et sa verification fail-closed; aucune auto-signature, aucun drapeau JSON manuel, aucune suppression du refus.

### Ecart technique entre revue et autorisation experimentale (audit statique VPS 2026-10-17)

- **Verifier de signature existant non reutilisable tel quel :** la fonction verify_signed_initial_review dans research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_prospective_causal_protocol_v1.py exige explicitement un paquet et un instrument BINANCE_COINM_BTCUSD_PERP, alors que ce dossier concerne Coinbase Exchange **spot BTC-USD / ETH-USD 2025-Q4**. Ne pas signer un avis BTC-ETH sous une fausse identite de produit et ne pas reutiliser cette fonction comme une approbation scientifique BTC-ETH.
- **La porte de recherche n'est pas la porte d'une unique experience :** v57_search_authorization_gate_v1.py ajoute systematiquement INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE et renvoie DENIED; si on levait arbitrairement le refus, son budget nominal autorise serait de **quatre candidats**, alors que ce protocole en prevoit UN. Ne supprimer ni le refus ni transformer un avis en activation automatique du Searcher.
- **Livrable requis AVANT une experience :** un rapport independant attribuable evaluant prior-art, donnees, chronologie, couts/short ETH, risques et limites retrospectives; l'empreinte du paquet v2 doit etre rattachee a ce rapport; l'identite, les qualifications et les conflits d'interets de l'evaluateur doivent etre documentes. Si un schema de signature est requis, son verificatif propre a BTC-ETH et sa chaine de confiance externe devront etre approuves et testes *separement* avant usage.
- **Permission experimentale separee, encore absente :** autorisation de revue scientifique limitee a UNE hypothese, une seule periode train-prefix, des fichiers de donnees/code/config empreintes, des couts de venue justifies, un budget fini, un arret en cas d'anomalie et zero ordre. Aucune nouvelle permission tant que cet accord independant et son enforcement fail-closed ne sont pas verifies. Une decision REJECT de l'evaluateur interdit naturellement toute experience.
- **Statut :** OBSERVATION TECHNIQUE VERIFIEE, PAS UNE REVUE EXTERNE. Aucun avis emis ni recu, aucune preuve de PF, aucune autorisation de recherche ou de trading.

**STOP de construction volontaire :** ne plus ajouter de variantes, features, sondes ou archives pour masquer ce verrou. Ne reprendre les modifications que pour une correction justifiee par l'avis scientifique reel ou pour une procedure de permission independante formellement revue. Ne pas lancer de backtest ni ouvrir le holdout.


- Version v1 historique conservée : stage03_btc_eth_independent_review_v1.zip, SHA-256 8213d887dde37f002cb93b1e2417b64ca73003246956d8b7c64997b6f5b81e9a.
- Le protocole et les metriques restent des instantanes; le code courant du calcul directionnel synthetique (commits 8e3ba28, eaf3673) est dans l archive v2.
