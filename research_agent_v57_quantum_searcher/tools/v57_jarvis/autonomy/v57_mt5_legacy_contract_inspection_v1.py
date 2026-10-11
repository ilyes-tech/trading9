#!/usr/bin/env python3
"""Read-only legacy MT5 contract inspection. Never reuses authorization."""
import json,sys
from pathlib import Path
P=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/deployment/mt5/V57_MT5_DEMO_EXECUTION_SURVIVOR_V1.json")
def main():
 if not P.is_file() or P.is_symlink():raise ValueError("LEGACY_CONFIG_MISSING")
 x=json.loads(P.read_text())
 required={"strategy_id","symbol","timeframe","side","signal","risk","execution_semantics","authorization"}
 missing=sorted(required-set(x))
 if missing:raise ValueError("MISSING_FIELDS:"+",".join(missing))
 signal=x["signal"];risk=x["risk"];execution=x["execution_semantics"]
 fields={"market":["symbol","timeframe","side"],"signal":["logic","thresholds"],"risk":["atr_window","atr_multiplier","rr","time_stop_bars"],"execution":["signal_on_closed_bar","entry","stop_target_replay_priority"]}
 checks={"market":all(x.get(k) is not None for k in fields["market"]),"signal":all(signal.get(k) is not None for k in fields["signal"]),"risk":all(risk.get(k) is not None for k in fields["risk"]),"execution":all(execution.get(k) is not None for k in fields["execution"])}
 out={"kind":"JARVIS_MT5_LEGACY_CONTRACT_INSPECTION_V1","status":"SCHEMA_INSPECTED" if all(checks.values()) else "INCOMPLETE","checks":checks,"legacy_demo_authorization_present":x.get("authorization",{}).get("demo_orders_allowed") is True,"legacy_strategy_id":x["strategy_id"],"reusable_as_new_strategy_config":False,"authorization_transfer_allowed":False,"orders_allowed":False,"mt5_allowed":False,"export_generated":False}
 print(json.dumps(out,sort_keys=True))
 if not all(checks.values()):sys.exit(3)
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|MT5_CONTRACT|"+type(e).__name__+":"+str(e));sys.exit(3)
