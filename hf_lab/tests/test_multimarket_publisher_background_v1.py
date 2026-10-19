"""Publisher citation metadata is a REVIEW INPUT, never admission or alpha."""
from pathlib import Path
import hashlib
import json
import runpy

ROOT=Path(__file__).resolve().parents[2]
AUTO=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
PROPOSER=runpy.run_path(str(AUTO/"v57_evidence_hypothesis_proposer_v1.py"))


def test_exactly_two_nontrading_publisher_context_records():
    records=PROPOSER["historical_volatility_background"]()
    assert len(records)==2
    assert {r["market"] for r in records}=={"EURUSD","XAUUSD"}
    assert len({r["hypothesis_id"] for r in records})==2
    assert all(r["bibliographic_role"]=="PUBLISHER_ABSTRACT_VOLATILITY_CONTEXT_ONLY" for r in records)
    assert all(r["status"]=="PUBLISHER_BIBLIOGRAPHY_REVIEW_ONLY_NOT_ADMITTED" for r in records)
    assert all(r["execution_authorized"] is False and r["orders_allowed"] is False for r in records)
    assert all(r["holdout_allowed"] is False and r["auto_promotion_allowed"] is False for r in records)


def test_no_directional_alpha_or_actual_instrument_equivalence_claimed():
    records=PROPOSER["historical_volatility_background"]()
    assert all("NOT_DIRECTIONAL_EDGE" in r["causal_dimension"] for r in records)
    assert all("TRADING_EDGE_UNPROVEN" in ",".join(r["missing_evidence"]) for r in records)
    assert all(r["paper_instrument"] != r["data_instrument"] for r in records)
    assert all(r["portability_issue"] for r in records)
    assert all("BROKER_FEES" in ",".join(r["missing_evidence"]) for r in records)


def test_bibliographic_hash_is_local_only_and_not_external_attestation():
    records=PROPOSER["historical_volatility_background"]()
    reference=PROPOSER["VOLATILITY_BACKGROUND_REFERENCES"]
    for source,record in zip(reference,records):
        assert record["source_fingerprint_type"]=="LOCAL_BIBLIOGRAPHIC_METADATA_NOT_INDEPENDENT_TEXT_ATTESTATION"
        expected=hashlib.sha256(
            json.dumps(source,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest()
        assert record["evidence_source_sha256"]==expected


def test_gold_and_fx_publications_have_distinct_dois_and_market_descriptions():
    records={r["market"]:r for r in PROPOSER["historical_volatility_background"]()}
    assert records["EURUSD"]["source_doi"]=="10.1111/0022-1082.85732"
    assert "mark" in records["EURUSD"]["paper_instrument"].lower()
    assert "pre-euro" in records["EURUSD"]["paper_instrument"]
    assert records["XAUUSD"]["source_doi"].startswith("10.1002/1096-9934")
    assert "COMEX" in records["XAUUSD"]["paper_instrument"]


def test_registry_marks_bibliography_as_background_not_trading_candidate():
    registry=runpy.run_path(str(AUTO/"v57_multimarket_candidate_registry_v1.py"))
    markets=("XAUUSD","BTCUSD","ETHUSD","LTCUSD","EURUSD","GBPUSD","USDJPY")
    inv={"kind":"V57_MULTIMARKET_CAPABILITY_INVENTORY_V1",
         "markets":[{"market":m} for m in markets]}
    features={"kind":"V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1",
              "markets":[{"market":m,"bar_imbalance_feature_schema_supported":False}
                         for m in markets]}
    proposals={"proposals":PROPOSER["historical_volatility_background"]()}
    agenda={"kind":"JARVIS_RESEARCH_AGENDA_V4","active":None,"items":[]}
    out=registry["build"](inv,proposals,features,agenda,frozenset())
    assert out["publisher_background_references"]==2
    assert out["admitted_trading_candidates"]==0
    for row in out["records"]:
        if row["hypothesis_id"]:
            assert row["literature_background_only"] is True
            assert row["status"]=="PUBLISHER_BIBLIOGRAPHY_ONLY_NO_DIRECTIONAL_HYPOTHESIS"
            assert row["execution_authorized"] is False
