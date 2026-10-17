"""Minimal Stage05 engineering tests; synthetic evidence and temporary memory only.

These tests do NOT operate JARVIS production memory, authorize research, or
validate a real-market hypothesis.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
AUTONOMY = ROOT / "research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"


def test_synthetic_learning_memory_ingest_is_idempotent():
    ingest = runpy.run_path(str(AUTONOMY / "v57_learning_memory_v2.py"))["ingest"]
    with TemporaryDirectory(prefix="omega-memory-unit-") as tmp:
        folder = Path(tmp) / "inputs"
        folder.mkdir()
        ingest.__globals__["DB"] = Path(tmp) / "memory.sqlite3"
        evidence = {
            "space": "SYNTHETIC_ONLY",
            "status": "SYNTHETIC_ENGINEERING_REJECT",
            "result": {
                "batches": [
                    {"candidates": [
                        {
                            "strategy_id": "SYNTHETIC_NEVER_ADMITTED",
                            "decision": "REJECT",
                            "deep_status": "NO_MARKET_EVIDENCE",
                        }
                    ]}
                ]
            },
        }
        (folder / "synthetic_test.json").write_text(json.dumps(evidence))
        assert ingest(folder) == (1, 1)
        assert ingest(folder) == (0, 1)


def test_synthetic_hypothesis_repeats_denied_new_requires_review():
    tools = runpy.run_path(str(AUTONOMY / "v57_hypothesis_history_dedup_v1.py"))
    example = {
        "hypothesis_id": "synthetic-1",
        "market": "SYNTHETIC",
        "space": "SYNTHETIC_PIPELINE",
        "causal_dimension": "CLOSED_BAR_DIRECTION",
        "native_family": "MOMENTUM",
        "objective": "ENGINEERING_ONLY",
        "parent_strategy_id": None,
    }
    history = {
        "ids": {example["hypothesis_id"]},
        "fingerprints": {tools["fingerprint"](example)},
    }
    classify = tools["classify"]
    assert classify(example, history) == "DENY_REPEATED_ID"
    assert classify(dict(example, hypothesis_id="synthetic-2"), history) == "DENY_REPEATED_CAUSAL_SIGNATURE"
    assert classify(dict(example, hypothesis_id="synthetic-3", causal_dimension="DISTINCT"), history) == "REVIEW_REQUIRED_NOT_AUTHORIZED"

def test_synthetic_stage03_to_stage05_replay_decision_memory_handoff():
    """One minimal deterministic data->replay->REJECT->memory proof."""
    from hf_lab.tools import omega_stage03_engineering_smoke_v1 as smoke

    ingest = runpy.run_path(str(AUTONOMY / "v57_learning_memory_v2.py"))["ingest"]
    with TemporaryDirectory(prefix="omega-vertical-unit-") as tmp:
        base = Path(tmp)
        ingest.__globals__["DB"] = base / "learning.sqlite3"
        replay_proof, count, signals, _ = smoke.exercise(
            base / "replay.sqlite3", smoke.synthetic_bars()
        )
        assert count == 83 and signals == 83
        evidence_dir = base / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "synthetic_reject.json").write_text(json.dumps({
            "kind": "SYNTHETIC_ENGINEERING_ONLY",
            "space": "SYNTHETIC_ONLY",
            "status": "ENGINEERING_PASS_SCIENCE_NOT_ADMITTED",
            "replay_fingerprint_sha256": replay_proof,
            "result": {"batches": [{"candidates": [{
                "strategy_id": "SYNTHETIC_PIPELINE_ONLY",
                "decision": "REJECT",
                "deep_status": "NO_INDEPENDENT_REAL_MARKET_EVIDENCE",
            }]}]},
            "research_execution_authorized": False,
            "orders_allowed": False,
        }, sort_keys=True))
        assert ingest(evidence_dir) == (1, 1)
        assert ingest(evidence_dir) == (0, 1)
