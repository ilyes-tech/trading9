import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
ALLOW={"multimarket_evidence_registry_v3.json":"V57_MULTIMARKET_EVIDENCE_REGISTRY_V3"}
def verify(candidate):
 if not isinstance(candidate,dict):return "DENY_MALFORMED"
 if candidate.get("new_causal_evidence_verified") is True:return "DENY_SELF_ATTESTED"
 name=candidate.get("evidence_file")
 if not isinstance(name,str) or name not in ALLOW:return "DENY_UNTRUSTED_SOURCE"
 p=S/name
 if not p.is_file() or p.is_symlink():return "DENY_MISSING_OR_SYMLINK"
 expected=candidate.get("evidence_sha256")
 if not isinstance(expected,str) or len(expected)!=64:return "DENY_HASH"
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected:return "DENY_HASH"
 try:doc=json.loads(raw)
 except (ValueError,UnicodeError):return "DENY_INVALID_JSON"
 if doc.get("kind")!=ALLOW[name] or doc.get("status")!="PASS" or len(doc.get("markets",{}))!=7:return "DENY_SCHEMA"
 if any(doc.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE_SOURCE"
 return "INTEGRITY_AND_SCHEMA_VERIFIED_NOT_CAUSAL_NOVELTY"

def assess_trade_robustness(folds, strategy_id):
    """Recompute legacy DEEP criteria from supplied stressed net trade records.

    Pure numeric review: no file access, replay, holdout or authorization.
    Caller must separately verify provenance, costs, selection and independence.
    Exactly three chronological folds; timestamps are UTC epoch seconds.
    """
    import math
    import numpy as np
    safe = dict(causal_novelty_proven=False, independent_replication_proven=False,
                new_research_authorized=False, orders_allowed=False,
                mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)
    def denied(reason):
        return dict(status='ROBUSTNESS_INPUT_REJECTED', reason=reason, **safe)
    if not isinstance(strategy_id, str) or len(strategy_id) != 64 or any(c not in '0123456789abcdef' for c in strategy_id):
        return denied('INVALID_STRATEGY_HASH')
    if not isinstance(folds, list) or len(folds) != 3:
        return denied('THREE_FOLDS_REQUIRED')
    if any(not isinstance(rows, list) or not rows for rows in folds):
        return denied('EMPTY_OR_MALFORMED_FOLD')
    if sum(len(rows) for rows in folds) > 100000:
        return denied('TRADE_BUDGET_EXCEEDED')
    normalized, last_fold_exit = [], -1
    for rows in folds:
        clean, last_exit = [], last_fold_exit
        for trade in rows:
            if not isinstance(trade, dict):
                return denied('MALFORMED_TRADE')
            entry, exit_, stress = (trade.get(k) for k in ('entry_time','exit_time','stress_net_bps'))
            if type(entry) is not int or type(exit_) is not int or not 0 <= entry < exit_ <= 253402300799:
                return denied('INVALID_TIMESTAMPS')
            if entry < last_exit:
                return denied('NONCHRONOLOGICAL_OR_OVERLAPPING_TRADES')
            if type(stress) not in (int,float):
                return denied('NONFINITE_RETURN')
            try:
                stress = float(stress)
            except (ValueError,OverflowError):
                return denied('NONFINITE_RETURN')
            if not math.isfinite(stress):
                return denied('NONFINITE_RETURN')
            clean.append((entry, exit_, stress)); last_exit = exit_
        normalized.append(clean); last_fold_exit = last_exit
    output, positive_halves = [], 0
    seed = int(strategy_id[:16],16) % (2**32)
    for index, rows in enumerate(normalized):
        groups = {}
        for entry, _, value in rows:
            g = groups.setdefault(entry // 86400, [0.0,0.0,0.0,0])
            g[0] += value; g[1] += max(value,0.0); g[2] += max(-value,0.0); g[3] += 1
        if len(groups) > 3660:
            return denied('DAY_BUDGET_EXCEEDED')
        g = np.asarray([groups[k] for k in sorted(groups)],dtype=float)
        if not np.isfinite(g).all():
            return denied('AGGREGATE_OVERFLOW')
        with np.errstate(over='ignore',invalid='ignore'):
            totals = g.sum(axis=0)
        if not np.isfinite(totals).all():
            return denied('AGGREGATE_OVERFLOW')
        max_trade = max(max(x[2],0.0) for x in rows) / totals[1] if totals[1] > 0 else 1.0
        positive_days = g[g[:,0] > 0,0]
        day_profit = float(positive_days.sum())
        max_day = float(positive_days.max()/day_profit) if day_profit > 0 else 1.0
        pmean = ppf = 0.0
        if len(groups) >= 2:
            rng = np.random.default_rng(seed+index); means = pfs = 0
            for _ in range(1000):
                ids = rng.integers(0,len(groups),size=len(groups))
                with np.errstate(over='ignore',invalid='ignore'):
                    sampled = g[ids].sum(axis=0)
                if not np.isfinite(sampled).all():
                    return denied('BOOTSTRAP_OVERFLOW')
                means += int(sampled[0] > 0)
                pfs += int(sampled[1] > 0 and sampled[1] >= sampled[2])
            pmean, ppf = means/1000, pfs/1000
        midpoint = (rows[0][0]+rows[-1][0])//2
        halves = [[x[2] for x in rows if x[0] <= midpoint], [x[2] for x in rows if x[0] > midpoint]]
        positives = sum(len(h) >= 10 and sum(h) > 0 for h in halves)
        positive_halves += positives
        output.append(dict(fold_index=index,trades=len(rows),days=len(groups),
                           p_mean_gt0=pmean,p_pf_ge1=ppf,positive_halves=positives,
                           max_trade_profit_share=float(max_trade),max_day_profit_share=max_day))
    checks = dict(bootstrap_mean=min(x['p_mean_gt0'] for x in output) >= 0.90,
                  bootstrap_pf=min(x['p_pf_ge1'] for x in output) >= 0.80,
                  positive_halves=positive_halves >= 4,
                  trade_concentration=max(x['max_trade_profit_share'] for x in output) <= 0.35,
                  day_concentration=max(x['max_day_profit_share'] for x in output) <= 0.50)
    return dict(status='ROBUSTNESS_PASS_NOT_ADMITTED' if all(checks.values()) else 'ROBUSTNESS_REJECT',
                strategy_id=strategy_id,bootstrap_draws=1000,folds=output,checks=checks,
                thresholds=dict(min_boot_mean_probability=0.90,min_boot_pf_probability=0.80,
                                min_positive_halves=4,max_trade_profit_share=0.35,max_day_profit_share=0.50),
                scope='SUPPLIED_STRESSED_RETURNS_ONLY_NOT_COST_OR_PROVENANCE_OR_NOVELTY_VERIFICATION',**safe)

def main():
 p=S/"multimarket_evidence_registry_v3.json";h=hashlib.sha256(p.read_bytes()).hexdigest()
 cases=[({"new_causal_evidence_verified":True},"DENY_SELF_ATTESTED"),({"evidence_file":"arbitrary_pass.json"},"DENY_UNTRUSTED_SOURCE"),({"evidence_file":p.name,"evidence_sha256":"0"*64},"DENY_HASH"),({"evidence_file":p.name,"evidence_sha256":h},"INTEGRITY_AND_SCHEMA_VERIFIED_NOT_CAUSAL_NOVELTY")]
 if any(verify(x)!=expected for x,expected in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_INDEPENDENT_EVIDENCE_VERIFIER_V2","status":"PASS","tests":len(cases),"allowlisted_sources":list(ALLOW),"source_sha256":h,"source_schema_checked":True,"trade_robustness_evaluation_supported":True,"causal_novelty_proven":False,"new_research_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"independent_evidence_verifier_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"independent_evidence_verifier_v2.json")
 print("ALL PASS|INDEPENDENT_EVIDENCE_VERIFIER_V2|TESTS=4|ALLOWLIST=1|NOVELTY=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|INDEPENDENT_EVIDENCE_VERIFIER_V2|"+str(e));sys.exit(3)
