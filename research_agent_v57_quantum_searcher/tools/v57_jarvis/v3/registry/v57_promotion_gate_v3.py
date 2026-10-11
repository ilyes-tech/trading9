ENGINE="V57_JARVIS_PROMOTION_GATE_V3"
def evaluate(validated_candidate,materialized_replay,provenance=True):
    pre=validated_candidate is True
    post=materialized_replay is True
    prov=provenance is True
    allowed=bool(pre and post and prov)
    return {"engine":ENGINE,"status":"PASS" if allowed else "BLOCKED","validated_candidate":pre,"materialized_exact_replay":post,"provenance":prov,"promotion_allowed":allowed,"orders_allowed":False,"mt5_launch_allowed":False}
