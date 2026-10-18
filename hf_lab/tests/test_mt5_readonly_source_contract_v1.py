"""Static protection checks for an uncompiled MQL5 draft. NOT execution proof."""
from pathlib import Path
import re

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "research_agent_v57_quantum_searcher"
    / "deployment"
    / "mt5"
    / "OMEGA_Mt5ReadOnlyBrokerSpec_v1.mq5"
)


def test_readonly_guard_requires_investor_demo_login():
    data = SOURCE.read_text()
    assert "void OnStart()" in data
    assert "ACCOUNT_TRADE_MODE_DEMO" in data
    assert "ACCOUNT_TRADE_ALLOWED" in data
    assert "TERMINAL_TRADE_ALLOWED" in data
    assert "NOT_CONNECTED" in data
    assert "INVESTOR_READONLY_LOGIN_AND_AUTOTRADING_OFF_REQUIRED" in data


def test_no_executable_order_or_network_api_used():
    data = SOURCE.read_text()
    # Direct-call patterns, including ones in comments, must remain absent.
    for item in ("OrderSend", "OrderCheck", "CTrade", "PositionOpen",
                 "WebRequest", "SocketConnect", "#import", "TerminalClose"):
        assert not re.search(r"\b" + re.escape(item) + r"\b", data)


def test_export_scope_does_not_claim_commission_or_real_fill():
    data = SOURCE.read_text()
    for market in ('"EURUSD"', '"GBPUSD"', '"USDJPY"', '"XAUUSD"'):
        assert market in data
    assert 'UNVERIFIED_REQUIRES_ACCOUNT_FEE_SCHEDULE' in data
    assert "CURRENT_TICK_ONLY_NOT_FILL" in data
    assert 'FILE_WRITE | FILE_CSV' in data
    assert "OrdersTotal" not in data
