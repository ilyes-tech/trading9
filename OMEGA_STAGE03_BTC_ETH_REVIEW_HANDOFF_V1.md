# OMEGA Stage03 BTC–ETH — dossier de revue indépendante (non approuvé)

Le dossier signé n’existe pas ; ceci est un envoi de preuves et de questions **sans autorisation**.

- Archive sur le VPS : `/home/trading/.local/state/tradingai/jarvis-autonomous/stage03_btc_eth_independent_review_v2.zip`
- SHA-256 archive : `d1a9e8e20f3d960a6f91c3fc289f17aad4337bcd19113a5dec82922e846c2e6a`
- Contenu : 9 fichiers sources existants, README et manifeste de hachages; module et tests mis à jour (18 tests synthétiques), contrôlés un par un.
- Pas de données brutes prix, données de validation, holdout, identifiants ni clés privées dans l’archive.
- Revue requise : originalité/antériorité, causalité, frais réels, possibilité du short ETH, qualité/provenance, portée rétrospective, autorisation indépendante.
- Aucun backtest nouveau ni ordre. La porte Searcher reste DENIED.

**Réponse externe attendue** : revue explicite avec corrections ou rejet motivé. Une revue favorable ne constitue pas à elle seule une autorisation d’expérience et ne modifie aucun garde-fou.

**Deux dependances distinctes et non satisfaites :**
1. Un evaluateur externe reel doit rendre un avis methodologique explicite sur ce protocole BTC-ETH; aucun avis signe ni autorite de revue BTC-ETH n'est disponible. Une publication sur le sujet n'est pas une evaluation de cette implementation.
2. La porte actuelle `v57_search_authorization_gate_v1.py` ajoute systematiquement `INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE`; il n'existe pas de voie BTC-ETH autonome deja approuvee pour signer et limiter UNE experience retrospective train-only. Meme un avis externe positif ne debloque pas automatiquement cette porte. Une autorite distincte doit approuver une voie de permission scientifique bornee et sa verification fail-closed; aucune auto-signature, aucun drapeau JSON manuel, aucune suppression du refus.

**STOP de construction volontaire :** ne plus ajouter de variantes, features, sondes ou archives pour masquer ce verrou. Ne reprendre les modifications que pour une correction justifiee par l'avis scientifique reel ou pour une procedure de permission independante formellement revue. Ne pas lancer de backtest ni ouvrir le holdout.


- Version v1 historique conservée : stage03_btc_eth_independent_review_v1.zip, SHA-256 8213d887dde37f002cb93b1e2417b64ca73003246956d8b7c64997b6f5b81e9a.
- Le protocole et les metriques restent des instantanes; le code courant du calcul directionnel synthetique (commits 8e3ba28, eaf3673) est dans l archive v2.
