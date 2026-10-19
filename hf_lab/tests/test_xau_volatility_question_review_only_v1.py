"""XAUUSD volatility question: pre-registration only, never directional alpha."""
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[2]
AUTO=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
Q=runpy.run_path(str(AUTO/"v57_multimarket_question_builder_v1.py"))
F=runpy.run_path(str(AUTO/"v57_multimarket_research_feedback_v1.py"))
D=runpy.run_path(str(AUTO/"v57_multimarket_decision_v1.py"))
P=runpy.run_path(str(AUTO/"v57_evidence_hypothesis_proposer_v1.py"))
MARKETS=("XAUUSD","BTCUSD","ETHUSD","LTCUSD","EURUSD","GBPUSD","USDJPY")


def cases():
    feature={"kind":"V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1",
             "execution_authorized":False,
             "markets":[{"market":m,"price_bar_march_schema_supported":True,
                         "bar_imbalance_feature_schema_supported":m in ("BTCUSD","ETHUSD","LTCUSD")}
                        for m in MARKETS]}
    prior={"kind":"V57_MULTIMARKET_NOVELTY_REVIEW_V1",
           "execution_authorized":False,
           "markets":[{"market":m,"historical_exhausted_count":0,
                       "historical_trial_count":None,
                       "historical_trial_scope":"NO_MATCH_IN_THIS_CAMPAIGN_NOT_PROOF_OF_NOVELTY"}
                      for m in MARKETS]}
    source={"kind":"V57_EVIDENCE_HYPOTHESIS_PROPOSALS_V1",
            "proposals":P["historical_volatility_background"]()}
    return feature,prior,source


def test_gold_scoped_falsifiable_question_is_not_strategy_or_order():
    feature,prior,source=cases()
    q=Q["build"](feature,prior,source)
    assert q["specified_count"]==4  # Gold volatility + existing crypto flow questions
    gold=next(x for x in q["questions"] if x["market"]=="XAUUSD")
    assert gold["status"]=="VOLATILITY_QUESTION_FOR_EXTERNAL_REVIEW_NOT_ADMITTED"
    assert gold["research_question_type"]=="NON_DIRECTIONAL_VOLATILITY_FORECAST"
    assert gold["source_role"]=="PUBLISHER_BACKGROUND_ONLY_NOT_TRADABLE_ALPHA"
    assert gold["costs_verified"] is False and gold["directional_edge_proven"] is False
    assert gold["independent_review_required"] is True
    assert gold["minimum_warmup_completed_returns"]==30
    assert "t+1" in gold["target"] and "t+1" not in gold["feature"]
    assert len(gold["hypothesis_id"])==64
    assert all(q[k] is False for k in ("execution_authorized","orders_allowed",
                                     "mt5_allowed","holdout_allowed","auto_promotion_allowed"))
    assert next(x for x in q["questions"] if x["market"]=="EURUSD")["hypothesis"] is None


def test_without_right_source_or_price_schema_gold_cannot_open():
    feature,prior,source=cases()
    for mutation in ("none","bad_doi","unverified_transfer","no_price"):
        local_feature={"kind":feature["kind"],"markets":[dict(m) for m in feature["markets"]]}
        local_source={"kind":source["kind"],"proposals":[dict(p) for p in source["proposals"]]}
        if mutation=="none":
            local_source=None
        elif mutation=="bad_doi":
            next(x for x in local_source["proposals"] if x["market"]=="XAUUSD")["source_doi"]="fabricated"
        elif mutation=="unverified_transfer":
            next(x for x in local_source["proposals"] if x["market"]=="XAUUSD")["portability_issue"]=None
        else:
            local_feature["markets"][0]["price_bar_march_schema_supported"]=False
        doc=Q["build"](local_feature,prior,local_source)
        assert doc["specified_count"]==3
        gold=doc["questions"][0]
        assert gold["status"]=="BLOCKED_MISSING_FEATURE_SCHEMA"
        assert gold["hypothesis"] is None
        assert doc["execution_authorized"] is False


def test_review_question_routes_through_feedback_and_multimarket_decision():
    feature,prior,source=cases()
    questions=Q["build"](feature,prior,source)
    registry={"kind":"V57_MULTIMARKET_CANDIDATE_REGISTRY_V1","markets_covered":7,
              "execution_authorized":False,
              "records":[{"market":m,"hypothesis_id":None,
                          "duplicate_rejected_strategy_id":False} for m in MARKETS]}
    fb=F["build"](registry,questions,prior)
    gold=next(x for x in fb["markets"] if x["market"]=="XAUUSD")
    assert gold["next_step"]=="REVIEW_XAU_VOLATILITY_PROTOCOL_INSTRUMENT_TRANSFER_AND_COSTS"
    inventory={"execution_authorized":False,"markets":[{"market":m} for m in MARKETS]}
    queue={"execution_authorized":False,
           "markets":[{"market":m,"bar_data_present":True} for m in MARKETS]}
    decision=D["decide"](inventory,queue,feature,prior,registry,fb)
    output={x["market"]:x["next_action"] for x in decision["markets"]}
    assert output["XAUUSD"]=="REVIEW_XAU_VOLATILITY_PROTOCOL_INSTRUMENT_TRANSFER_AND_COSTS"
    assert output["EURUSD"]=="REVIEW_PRICE_BAR_HYPOTHESIS_AND_EXECUTABLE_BROKER_COSTS"
    assert decision["admitted_hypotheses"]==0
    assert decision["search_executed"] is False
    for k in ("orders_allowed","holdout_allowed","mt5_allowed","execution_authorized"):
        assert decision[k] is False
