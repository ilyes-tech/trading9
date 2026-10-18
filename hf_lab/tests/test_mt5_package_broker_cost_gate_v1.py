"""Synthetic safety tests: MT5 packaging must not trust archived demo spreads."""
import json
import hashlib
from pathlib import Path
import runpy

SCRIPT=Path(__file__).resolve().parents[2]/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_mt5_package_readiness_v1.py"
NS=runpy.run_path(str(SCRIPT))
BLOCKERS=NS["broker_cost_blockers"]


def archived():
    return {
        "status":"PASS_ARCHIVED_DEV_SPREAD_PROVENANCE_ONLY_BROKER_COST_BINDING_INCOMPLETE",
        "scientific_admission":False,"orders_allowed":False,"holdout_read":False,
    }


def connection():
    return {
        "status":"VERIFIED_READONLY_DEMO_BROKER_ACCOUNT",
        "account_specific_broker_authenticated":True,
        "broker_server_selected":True,
        "server":"SYNTHETIC_DEMO_TEST_ONLY",
        "account_ref_hash":"a"*64,
    }


def cost():
    return {
        "kind":"OMEGA_MT5_BROKER_COST_INPUT_BINDING_V1",
        "status":"BROKER_ACCOUNT_COST_INPUTS_VERIFIED_FOR_REVIEW_ONLY",
        "server":"SYNTHETIC_DEMO_TEST_ONLY",
        "account_ref_hash":"a"*64,
        "commission_for_account_verified":True,
        "bid_ask_spread_for_account_verified":True,
        "swap_for_account_verified":True,
        "fill_policy_for_account_verified":True,
        "orders_allowed":False,
        "holdout_read":False,
        "scientific_admission":False,
    }



def synthetic_export():
    return {
        "kind":"OMEGA_MT5_READONLY_ACCOUNT_COST_EXPORT_V1",
        "read_only":True, "orders_sent":False,
        "server":"SYNTHETIC_DEMO_TEST_ONLY", "account_ref_hash":"a"*64,
        "synthetic_fixture":True,
    }


def linked_cost():
    d=cost()
    d["source_export_sha256"]=hashlib.sha256(
        NS["canon"](synthetic_export()).encode()).hexdigest()
    return d


def test_no_broker_account_or_cost_file_is_rejected():
    reasons=BLOCKERS(None,archived(),None,None)
    assert "MT5_DEMO_BROKER_CONNECTION_UNVERIFIED" in reasons
    assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in reasons


def test_old_metaquotes_spreads_not_accepted_as_broker_cost():
    reasons=BLOCKERS(connection(),archived(),archived(),synthetic_export())
    assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in reasons


def test_bare_flags_not_enough_and_matching_synthetic_export_is_review_only():
    c=cost()
    assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in BLOCKERS(
        connection(),archived(),c,synthetic_export())
    c=linked_cost()
    reasons=BLOCKERS(connection(),archived(),c,synthetic_export())
    # Matching user-created SHA256 is integrity, not broker authenticity.
    assert "MT5_BROKER_COST_SOURCE_AUTHENTICITY_NOT_VERIFIED" in reasons
    assert reasons == ["MT5_BROKER_COST_SOURCE_AUTHENTICITY_NOT_VERIFIED"]
    # Pure synthetic tests verify data binding only, NOT account authentication.
    assert c["orders_allowed"] is False



def test_broker_server_mismatch_denied_even_with_claimed_attestation():
    c=linked_cost()
    c["server"]="DIFFERENT_DEMO"
    assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in BLOCKERS(connection(),archived(),c,synthetic_export())


def test_unverified_venue_fee_components_deny():
    for key in ("commission_for_account_verified","bid_ask_spread_for_account_verified",
                "swap_for_account_verified","fill_policy_for_account_verified"):
        c=linked_cost()
        c[key]=False
        assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in BLOCKERS(connection(),archived(),c,synthetic_export())


def test_invalid_historical_spread_or_safety_mutation_rejected():
    bad=archived()
    bad["orders_allowed"]=True
    assert "ARCHIVED_SPREAD_PROVENANCE_UNVERIFIED" in BLOCKERS(connection(),bad,cost(),synthetic_export())


def test_package_writer_in_synthetic_state_stays_blocked(tmp_path):
    scope=dict(NS)
    # run_path function globals can be safely substituted without touching VPS state.
    main=NS["main"]
    originals=main.__globals__["S"]
    main.__globals__["S"]=tmp_path
    try:
        main()
        d=json.loads((tmp_path/"mt5_package_readiness_v1.json").read_text())
        assert d["status"]=="BLOCKED"
        assert "MT5_DEMO_BROKER_CONNECTION_UNVERIFIED" in d["reasons"]
        assert "MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED" in d["reasons"]
        assert d["orders_allowed"] is False and d["mt5_allowed"] is False
        assert d["auto_promotion_allowed"] is False
    finally:
        main.__globals__["S"]=originals


def test_arbitrarily_claimed_external_trust_cannot_bypass_source_authenticity():
    c=linked_cost()
    c["independent_source_attestation_verified"]=True
    c["issuer_key_trusted_and_pinned"]=True
    x=synthetic_export()
    x["attested_by"]="SYNTHETIC_FABRICATED_SIGNER"
    c["source_export_sha256"]=hashlib.sha256(NS["canon"](x).encode()).hexdigest()
    reasons=BLOCKERS(connection(),archived(),c,x)
    assert "MT5_BROKER_COST_SOURCE_AUTHENTICITY_NOT_VERIFIED" in reasons
    assert reasons != []
