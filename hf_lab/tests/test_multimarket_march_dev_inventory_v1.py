"""No holdout: archive MARCH discovery doesn't imply order-flow eligibility."""
from pathlib import Path
import hashlib
import runpy

import pytest

SCRIPT=(Path(__file__).resolve().parents[2] /
        "research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_multimarket_capability_inventory_v1.py")
M=runpy.run_path(str(SCRIPT))


def test_inventory_accepts_verified_march_dev_for_forex_and_gold_not_only_kraken(tmp_path):
    root=tmp_path/"micro"
    root.mkdir()
    (root/"LTCUSD_MICRO_2026_03_M1.csv").write_text("header\n")
    (root/"LTCUSD_MICRO_2026_04_M1.csv").write_text("RESERVED_NEVER_READ\n")
    archive={m:{"file":"verified_march_fixture", "sha256":"a"*64,
                "scope":"2026-03_ONLY_DEV_M1"}
             for m in ("XAUUSD","BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY")}
    result=M["inventory"](root=root,march_sources=archive)
    assert len(result)==7
    assert all(x["bar_data_present"] for x in result)
    bymarket={x["market"]:x for x in result}
    assert bymarket["EURUSD"]["bar_files"]==[]
    assert bymarket["EURUSD"]["microbar_march_present"] is False
    assert bymarket["EURUSD"]["verified_historical_march_dev_source"]["scope"]=="2026-03_ONLY_DEV_M1"
    assert bymarket["LTCUSD"]["bar_files"]==["LTCUSD_MICRO_2026_03_M1.csv"]
    assert all("2026_04" not in str(x["bar_files"]) for x in result)
    assert all(x["execution_authorized"] is False for x in result)
    assert all(x["scientific_admission"] is False for x in result)
    assert all(x["feature_schema_verified"] is False for x in result)


def test_inventory_no_files_means_no_data(tmp_path):
    result=M["inventory"](root=tmp_path,march_sources={})
    assert all(x["bar_data_present"] is False for x in result)
    assert all(x["status"]=="NO_LOCAL_MARCH_DEV_BAR_DATA" for x in result)


def test_immutable_source_manifest_rejects_modification_before_data_access(tmp_path):
    m=tmp_path/"fake_manifest.json"
    m.write_text('{"entries": []}')
    with pytest.raises(ValueError,match="FROZEN_DEV_MANIFEST_SHA256_CHANGED"):
        M["verified_march_development"](repo=tmp_path,manifest_path=m)
    m.unlink()
    with pytest.raises(ValueError,match="FROZEN_DEV_MANIFEST_NOT_AVAILABLE"):
        M["verified_march_development"](repo=tmp_path,manifest_path=m)


def test_live_march_manifest_filenames_sha256_only():
    """Only the development-month sources are checked, never later months."""
    manifest=M["MANIFEST"]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest()==M["MANIFEST_SHA256"]
    checked=M["verified_march_development"]()
    assert len(checked)==6
    for market, rec in checked.items():
        assert rec["scope"]=="2026-03_ONLY_DEV_M1"
        assert rec["source"]=="FROZEN_V56_MARCH_MANIFEST"
        assert rec["sha256"] and len(rec["sha256"])==64
        assert "2026_04" not in rec["file"] and "2026_05" not in rec["file"]
        assert "2026_06" not in rec["file"]
