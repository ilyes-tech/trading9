"""Frozen V433 candidate cannot escape post-calibration or science gates."""
from pathlib import Path
import copy
import runpy

import pytest

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_finishing_decisions_v1.py"
NS=runpy.run_path(str(MODULE))
SID="a5fbb3e5389e0bd25bb170b87dfe5bb5dc7c4c2b0694b72ad606e3c7b2842e39"


def test_actual_frozen_candidate_rejected_by_existing_postcal_forensics():
    decision=NS["archived_survivor_decision"]()
    assert decision["strategy_id"]==SID
    assert decision["decision"]=="REJECT_POST_CALIBRATION_REPLAY"
    assert decision["post_calibration_conclusion"]=="POST_CALIBRATION_REPLAY_FAIL"
    assert decision["post_calibration_fixed_exact_pass"] is False
    assert decision["post_calibration_evidence_sha256"]=="8e3e0ce372277224e9e0a4ed974c5f271ce4d5e67723a24cc4196d212bc8e41c"
    assert decision["engineering_reference_only"] is True
    assert decision["scientific_admission"] is False
    assert all(decision[k] is False for k in ("orders_allowed","holdout_allowed","mt5_allowed"))


def test_forged_or_incomplete_postcal_cannot_pass_as_forensic_evidence(monkeypatch):
    real_module=runpy.run_path(str(ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/registry/v57_strategy_forensics_v2.py"))
    original=real_module["inspect"]()
    source_run_path=NS["runpy"].run_path

    def fake_forensics(path):
        if str(path).endswith("v57_strategy_forensics_v2.py"):
            return {"inspect":lambda: forged}
        return source_run_path(path)

    monkeypatch.setattr(NS["runpy"],"run_path",fake_forensics)
    for field,value in (
        ("same_strategy_id",False),
        ("provenance_all_pass",False),
        ("status","STOP"),
    ):
        forged=copy.deepcopy(original)
        forged[field]=value
        with pytest.raises(RuntimeError,match="ARCHIVED_SURVIVOR_EVIDENCE_NOT_VERIFIED"):
            NS["archived_survivor_decision"]()
    forged=copy.deepcopy(original)
    forged["post_calibration_performance_replay"]["evidence_valid"]=False
    with pytest.raises(RuntimeError,match="ARCHIVED_SURVIVOR_EVIDENCE_NOT_VERIFIED"):
        NS["archived_survivor_decision"]()


def test_even_legitimate_postcal_pass_never_grants_sci_admission(monkeypatch):
    result=runpy.run_path(str(ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/registry/v57_strategy_forensics_v2.py"))["inspect"]()
    result["post_calibration_performance_replay"]["conclusion"]="POST_CALIBRATION_REPLAY_PASS"
    monkeypatch.setattr(NS["runpy"],"run_path",lambda _:{"inspect":lambda:result})
    row=NS["archived_survivor_decision"]()
    assert row["decision"]=="EXTERNAL_SCIENTIFIC_REVIEW_REQUIRED_NOT_AUTHORIZED"
    assert row["scientific_admission"] is False
    assert row["orders_allowed"] is False
    assert row["mt5_allowed"] is False
