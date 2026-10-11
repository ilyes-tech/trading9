#!/usr/bin/env python3
import hashlib,json,pathlib,sys
ROOT=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher')
MANIFEST=ROOT/'work/v57_jarvis/V57_JARVIS_CORE_FREEZE_V1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 try:m=json.loads(MANIFEST.read_text())
 except Exception as e:print('STOP|FAIL|CORE_FREEZE_GUARD|MANIFEST_UNREADABLE|'+type(e).__name__);return 3
 sig=m.get('manifest_payload_sha256'); body=dict(m);body.pop('manifest_payload_sha256',None)
 calc=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 if not sig or sig!=calc:print('STOP|FAIL|CORE_FREEZE_GUARD|MANIFEST_HASH_MISMATCH');return 3
 for rel,expected in sorted(m.get('components_sha256',{}).items()):
  p=ROOT/rel
  if not p.is_file():print('STOP|FAIL|CORE_FREEZE_GUARD|MISSING|'+rel);return 3
  if sha(p)!=expected:print('STOP|FAIL|CORE_FREEZE_GUARD|COMPONENT_HASH_MISMATCH|'+rel);return 3
 inv=m.get('invariants',{})
 required=('execution_allowed','orders_allowed','mt5_allowed','holdout_read','real_orders_allowed','demo_orders_allowed','auto_promotion')
 if any(inv.get(k) is not False for k in required):print('STOP|FAIL|CORE_FREEZE_GUARD|INVARIANT_OPEN');return 3
 print('ALL PASS|CORE_FREEZE_GUARD|MANIFEST='+sig+'|COMPONENTS='+str(len(m.get('components_sha256',{})))+'|INVARIANTS=CLOSED');return 0
if __name__=='__main__':sys.exit(main())
