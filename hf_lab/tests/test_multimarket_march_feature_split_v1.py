"""March development only: price bars do not imply signed flow or broker execution."""
import copy
import runpy
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
I=runpy.run_path(str(A/"v57_multimarket_capability_inventory_v1.py"))
F=runpy.run_path(str(A/"v57_multimarket_feature_eligibility_v1.py"))


def doc(rows):
    return {"kind":"V57_MULTIMARKET_CAPABILITY_INVENTORY_V1",
            "later_month_files_read":False,"holdout_allowed":False,"markets":rows}


def test_real_sha_verified_march_price_bars_seven_markets_and_three_flow_markets():
    markets=I["inventory"]()
    rows=F["inspect"](doc(markets))
    assert {x["market"] for x in rows}==set(I["MARKETS"])
    assert {x["market"] for x in rows if x["price_bar_march_schema_supported"]}==set(I["MARKETS"])
    assert {x["market"] for x in rows if x["bar_imbalance_feature_schema_supported"]}=={
        "BTCUSD","ETHUSD","LTCUSD"}
    for r in rows:
        assert r["price_data_is_broker_executable"] is False
        assert r["research_authorized"] is False
        assert r["novelty_verified"] is False


def test_refuse_archive_hash_mismatch_without_changing_file():
    markets=I["inventory"]()
    altered=copy.deepcopy(markets)
    x=next(r for r in altered if r["market"]=="XAUUSD")
    x["verified_historical_march_dev_source"]["sha256"]="0"*64
    with pytest.raises(ValueError,match="MARCH_ARCHIVE_SHA256_CHANGED"):
        F["inspect"](doc(altered))


def test_only_march_microbar_header_read_and_future_files_ignored(tmp_path):
    root=tmp_path/"source"
    root.mkdir()
    (root/"LTCUSD_MICRO_2026_03_M1.csv").write_text(
        "time,open,high,low,close,volume,buy_volume,sell_volume\n")
    (root/"LTCUSD_MICRO_2026_04_M1.csv").write_text("RESERVED_DO_NOT_READ\n")
    one={"market":"LTCUSD", "bar_files":["LTCUSD_MICRO_2026_03_M1.csv"],
         "bar_data_present":True,"verified_historical_march_dev_source":None}
    rows=F["inspect"](doc([one]),root=root,repo=tmp_path)
    assert rows[0]["price_bar_march_schema_supported"] is True
    assert rows[0]["bar_imbalance_feature_schema_supported"] is True
    bad=copy.deepcopy(one)
    bad["bar_files"]=["LTCUSD_MICRO_2026_04_M1.csv"]
    with pytest.raises(ValueError,match="UNAUTHORIZED_MICROBAR_PERIOD"):
        F["inspect"](doc([bad]),root=root,repo=tmp_path)


def test_missing_march_boundary_is_rejected_before_data_read():
    with pytest.raises(ValueError,match="DEVELOPMENT_ONLY_BOUNDARY_NOT_CERTIFIED"):
        F["inspect"]({"kind":"V57_MULTIMARKET_CAPABILITY_INVENTORY_V1",
                      "markets":[],"holdout_allowed":False})
