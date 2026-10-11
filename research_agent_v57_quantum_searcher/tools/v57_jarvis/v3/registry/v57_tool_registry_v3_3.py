import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ALLOW={"SCIENTIST":"v57_scientist_v3_1.py","PROMOTION_GATE":"v57_promotion_gate_v3_3.py"}
def _load(name):
    if name not in ALLOW: return None
    p=HERE/ALLOW[name]
    if not p.is_file(): raise RuntimeError("TOOL_MODULE_MISSING:"+name)
    s=importlib.util.spec_from_file_location("j57v32_"+name.lower(),p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def run(name,payload=None):
    payload={} if payload is None else dict(payload)
    m=_load(name)
    if m is None: return {"status":"DENIED","reason":"TOOL_NOT_ALLOWLISTED","tool":name,"orders_allowed":False,"mt5_launch_allowed":False}
    if name=="SCIENTIST": return m.experiment(payload.get("hypothesis",""),int(payload.get("start",0)),int(payload.get("count",1)),bool(payload.get("evaluate",False)),int(payload.get("seed",574351)))
    if name=="PROMOTION_GATE":
        r=m.evaluate(payload.get("pre_validation"),payload.get("materialized_replay"),payload.get("provenance"))
        if r.get("promotion_allowed") is not False or r.get("self_promotion_allowed") is not False: raise RuntimeError("AUTO_PROMOTION_INVARIANT_BROKEN")
        return r
    return {"status":"DENIED","reason":"NO_HANDLER","orders_allowed":False,"mt5_launch_allowed":False}

import v57_critic_v3_4 as CRITIC

def critic(hypothesis):
    return CRITIC.critique(hypothesis)
