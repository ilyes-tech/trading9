import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ALLOW={"SCIENTIST":"v57_scientist_v3.py","PROMOTION_GATE":"v57_promotion_gate_v3.py"}
def _load(name):
    if name not in ALLOW: return None
    p=HERE/ALLOW[name]; s=importlib.util.spec_from_file_location("j57v3_"+name.lower(),p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def run(name,payload=None):
    payload={} if payload is None else dict(payload)
    m=_load(name)
    if m is None: return {"status":"DENIED","reason":"TOOL_NOT_ALLOWLISTED","tool":name}
    if name=="SCIENTIST": return m.experiment(payload.get("hypothesis",""),int(payload.get("start",0)),int(payload.get("count",1)),bool(payload.get("evaluate",False)))
    if name=="PROMOTION_GATE": return m.evaluate(payload.get("validated_candidate") is True,payload.get("materialized_replay") is True,payload.get("provenance") is True)
    return {"status":"DENIED","reason":"NO_HANDLER"}
