"""Synthetic-only memory->registry->feedback->decision anti-replay contract."""
from pathlib import Path
import runpy
import sqlite3

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUTO = ROOT / "research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
R = runpy.run_path(str(AUTO / "v57_multimarket_candidate_registry_v1.py"))
F = runpy.run_path(str(AUTO / "v57_multimarket_research_feedback_v1.py"))
D = runpy.run_path(str(AUTO / "v57_multimarket_decision_v1.py"))
MARKETS = ("XAUUSD", "BTCUSD", "ETHUSD", "LTCUSD", "EURUSD", "GBPUSD", "USDJPY")
REJECTED_ID = "LTCUSD_KRAKEN_CLOSED_M1_TAKER_BUY_DOMINANCE_LONG_15M_V1"
UNRELATED_ID = "INDEPENDENT_DISSIMILAR_HYPOTHESIS"


def test_existing_sqlite_rejections_read_only_and_exact(tmp_path):
    db = tmp_path / "memory.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE observations(strategy_id TEXT, decision TEXT)")
        conn.executemany("INSERT INTO observations VALUES (?,?)", [
            (REJECTED_ID, "REJECT"),
            ("XAUUSD_EXACT_REJECTED", "REJECTED_DEEP"),
            ("UNRELATED_ACCEPTED", "PASS"),
            (None, "REJECTED_PRIOR_TRAIN"),
        ])
    before = db.read_bytes()
    ids = R["rejected_strategy_ids"](db)
    assert ids == frozenset({REJECTED_ID, "XAUUSD_EXACT_REJECTED"})
    assert db.read_bytes() == before
    with pytest.raises(ValueError, match="REJECTION_HISTORY_UNAVAILABLE"):
        R["rejected_strategy_ids"](tmp_path / "missing.sqlite3")
    link = tmp_path / "link.sqlite3"
    link.symlink_to(db)
    with pytest.raises(ValueError, match="REJECTION_HISTORY_UNAVAILABLE"):
        R["rejected_strategy_ids"](link)


def test_exact_rejection_propagates_to_final_decision_without_new_authorization():
    inventory = {"kind": "V57_MULTIMARKET_CAPABILITY_INVENTORY_V1",
                 "execution_authorized": False,
                 "markets": [{"market": m} for m in MARKETS]}
    feature = {"kind": "V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1",
               "execution_authorized": False,
               "markets": [{"market": m, "bar_imbalance_feature_schema_supported": True} for m in MARKETS]}
    queue = {"kind": "V57_MULTIMARKET_RESEARCH_QUEUE_V1",
             "execution_authorized": False,
             "markets": [{"market": m, "bar_data_present": True} for m in MARKETS]}
    proposals = {"proposals": [
        {"market": "LTCUSD", "hypothesis_id": REJECTED_ID, "source_doi": "synthetic.test"},
        {"market": "BTCUSD", "hypothesis_id": UNRELATED_ID, "source_doi": "synthetic.test"},
    ]}
    agenda = {"kind": "JARVIS_RESEARCH_AGENDA_V4", "active": None, "items": []}
    registry = R["build"](inventory, proposals, feature, agenda,
                          frozenset({REJECTED_ID, "EXPERIMENT_NOT_IN_CURRENT_QUEUE"}))
    assert registry["rejection_history_read"] is True
    assert registry["rejected_exact_id_proposals"] == 1
    byid = {r["hypothesis_id"]: r for r in registry["records"] if r["hypothesis_id"]}
    assert byid[REJECTED_ID]["status"] == "HISTORICALLY_REJECTED_EXACT_STRATEGY_ID"
    assert byid[REJECTED_ID]["execution_authorized"] is False
    assert byid[UNRELATED_ID]["duplicate_rejected_strategy_id"] is False
    assert byid[UNRELATED_ID]["status"] == "NOVELTY_AND_CAUSAL_EVIDENCE_UNVERIFIED"
    hist = {"kind": "V57_MULTIMARKET_NOVELTY_REVIEW_V1",
            "execution_authorized": False,
            "markets": [
                {"market": m, "historical_exhausted_count": 0,
                 "historical_trial_count": None, "historical_sixty_second_trial_count": None,
                 "historical_trial_scope": "NO_MATCH_IN_THIS_CAMPAIGN_NOT_PROOF_OF_NOVELTY"}
                for m in MARKETS
            ]}
    questions = {"kind": "V57_MULTIMARKET_QUESTION_BUILDER_V1",
                 "questions": [
                     {"market": m, "status": "SYNTHETIC",
                      "hypothesis": "SYNTHETIC" if m in ("LTCUSD", "BTCUSD") else None,
                      "hypothesis_id": REJECTED_ID if m == "LTCUSD" else
                      (UNRELATED_ID if m == "BTCUSD" else None)}
                     for m in MARKETS
                 ]}
    feedback = F["build"](registry, questions, hist)
    f = {x["market"]: x for x in feedback["markets"]}
    assert f["LTCUSD"]["exact_strategy_memory_reject"] is True
    assert f["LTCUSD"]["next_step"] == "STOP_REJECTED_EXACT_STRATEGY_ID_FROM_MEMORY"
    assert f["BTCUSD"]["exact_strategy_memory_reject"] is False
    outcome = D["decide"](inventory, queue, feature, hist, registry, feedback)
    decision = {x["market"]: x for x in outcome["markets"]}
    assert decision["LTCUSD"]["next_action"] == "STOP_REJECTED_EXACT_STRATEGY_ID_FROM_MEMORY"
    assert decision["BTCUSD"]["next_action"] != "STOP_REJECTED_EXACT_STRATEGY_ID_FROM_MEMORY"
    assert outcome["search_executed"] is False
    assert outcome["admitted_hypotheses"] == 0
    assert outcome["orders_allowed"] is False
    assert outcome["holdout_allowed"] is False
    assert outcome["execution_authorized"] is False
