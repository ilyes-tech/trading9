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


def test_export_never_overwrites_previous_snapshot_and_requires_server_before_fileopen():
    data = SOURCE.read_text()
    assert 'EXPORT_ALREADY_EXISTS_NO_OVERWRITE' in data
    assert 'FileIsExist(export_name)' in data
    assert data.index('AccountInfoString(ACCOUNT_SERVER)') < data.index('FileOpen(')
    assert data.index('FileIsExist(export_name)') < data.index('FileOpen(')
    assert data.index('BROKER_SERVER_MISSING') < data.index('FileOpen(')


def test_empty_quote_export_cannot_claim_completion():
    data = SOURCE.read_text()
    assert 'if(rows == 0)' in data
    assert 'NO_VALID_QUOTES_HEADER_ONLY_EXPORT_NOT_EVIDENCE' in data
    assert data.index('if(rows == 0)') < data.index('OMEGA_READONLY_EXPORT_COMPLETED_BUT_NOT_COST_VERIFIED')


def test_export_rejects_stale_or_future_mt5_quote_and_retains_tick_time():
    data=SOURCE.read_text()
    assert 'SymbolInfoTick(symbol, tick)' in data
    assert 'datetime now_server = TimeTradeServer()' in data
    assert '(long)now_server - (long)tick.time' in data
    assert 'tick_server_time' in data
    assert 'TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS)' in data
    assert 'CLIENT-ESTIMATED and not independent NTP proof' in data
    assert 'quote_age_seconds > 120' in data
    assert 'quote_age_seconds < -120' in data
    assert 'STALE_OR_FUTURE_TICK_UNVERIFIED_CLOCK' in data
    assert data.index('if(!received ||') < data.index('quote_age_seconds = ')
    assert 'TimeToString(tick.time, TIME_DATE | TIME_SECONDS)' in data
    assert data.index('STALE_OR_FUTURE_TICK_UNVERIFIED_CLOCK') < data.index('FileWrite(output,\n                TimeToString(TimeGMT()')
    assert 'not independent NTP proof' in data


def test_export_scope_does_not_claim_commission_or_real_fill():
    data = SOURCE.read_text()
    for market in ('"EURUSD"', '"GBPUSD"', '"USDJPY"', '"XAUUSD"'):
        assert market in data
    assert 'UNVERIFIED_REQUIRES_ACCOUNT_FEE_SCHEDULE' in data
    assert "CURRENT_TICK_ONLY_NOT_FILL" in data
    assert 'FILE_WRITE | FILE_CSV' in data
    assert "OrdersTotal" not in data
