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


def audit_replay_costs(trades, fee_bps_per_side, slippage_bps_per_side):
    """Reconcile hf_lab TradeResult dictionaries; R units stay R units.

    Arithmetic verification only; assumed costs are not calibrated market costs.
    No conversion to the stressed-bps robustness contract is performed here.
    """
    import math
    def finite(value):
        if type(value) not in (int,float): return False
        try: return math.isfinite(value)
        except OverflowError: return False
    def result(status, reason=None, count=0):
        return dict(status=status,reason=reason,trades_checked=count,cost_realism_verified=False,
                    independent_replication_proven=False,new_research_authorized=False,
                    orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
    if not all(finite(x) and 0 <= x < 10000 for x in (fee_bps_per_side,slippage_bps_per_side)):
        return result('COST_REJECT','INVALID_COST_SETTINGS')
    if not isinstance(trades,list) or not 1 <= len(trades) <= 100000:
        return result('COST_REJECT','EMPTY_OR_OVERSIZE_TRADES')
    price_keys=('raw_entry_price','entry_price','raw_exit_price','exit_price','stop_price')
    metric_keys=('gross_r','fee_r','slippage_r','net_r')
    for index,t in enumerate(trades):
        if not isinstance(t,dict) or t.get('side') not in ('BUY','SELL'):
            return result('COST_REJECT','INVALID_TRADE',index)
        if not all(finite(t.get(k)) and t[k]>0 for k in price_keys) or not all(finite(t.get(k)) for k in metric_keys):
            return result('COST_REJECT','INVALID_NUMERIC_FIELDS',index)
        direction=1 if t['side']=='BUY' else -1
        raw_entry,raw_exit=t['raw_entry_price'],t['raw_exit_price']
        risk=direction*(raw_entry-t['stop_price'])
        if risk<=0:return result('COST_REJECT','INVALID_RISK_DISTANCE',index)
        entry=raw_entry*(1+direction*slippage_bps_per_side/10000)
        exit_=raw_exit*(1-direction*slippage_bps_per_side/10000)
        gross=direction*(raw_exit-raw_entry)/risk
        fee=(entry+exit_)*fee_bps_per_side/10000/risk
        slip=(abs(entry-raw_entry)+abs(exit_-raw_exit))/risk
        expected=dict(entry_price=entry,exit_price=exit_,gross_r=gross,fee_r=fee,slippage_r=slip,net_r=gross-fee-slip)
        if not all(finite(x) for x in expected.values()):
            return result('COST_REJECT','ARITHMETIC_OVERFLOW',index)
        for key,value in expected.items():
            if not math.isclose(t[key],value,rel_tol=1e-10,abs_tol=1e-10):
                return result('COST_REJECT','MISMATCH_'+key.upper(),index)
    return result('COST_ARITHMETIC_VERIFIED_NOT_ADMITTED',count=len(trades))


def audit_trade_evidence_file(candidate):
    """Reuse bounded JSON/hash checking; bind a cost report to expected hashes.

    Expected hashes must come from a separately reviewed manifest. This does not
    prove dataset contents, preregistration, independent selection or causality.
    """
    import importlib.util
    def reject(reason):
        return dict(status='TRADE_EVIDENCE_REJECTED',reason=reason,new_research_authorized=False,
                    independent_replication_proven=False,orders_allowed=False,mt5_allowed=False,
                    holdout_allowed=False,auto_promotion_allowed=False)
    if not isinstance(candidate,dict):return reject('MALFORMED_CANDIDATE')
    for key in ('strategy_sha256','dataset_sha256'):
        value=candidate.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            return reject('INVALID_'+key.upper())
    path=Path(__file__).with_name('v57_causal_evidence_files_v1.py')
    spec=importlib.util.spec_from_file_location('_omega_evidence_files',path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.ROOT=S
    status,doc=helper.check_file(candidate.get('evidence_file'),candidate.get('evidence_sha256'))
    if status!='FILE_INTEGRITY_VERIFIED':return reject(status)
    if doc.get('kind')!='V57_REPLAY_TRADE_COST_EVIDENCE_V1':return reject('INVALID_KIND')
    for key in ('strategy_sha256','dataset_sha256'):
        if doc.get(key)!=candidate[key]:return reject('MISMATCH_'+key.upper())
    settings=doc.get('settings')
    if not isinstance(settings,dict):return reject('MISSING_COST_SETTINGS')
    audit=audit_replay_costs(doc.get('trades'),settings.get('fee_bps_per_side'),settings.get('slippage_bps_per_side'))
    if audit['status']!='COST_ARITHMETIC_VERIFIED_NOT_ADMITTED':return reject(audit['reason'])
    return dict(audit,status='FILE_AND_COST_ARITHMETIC_VERIFIED_NOT_ADMITTED',
                evidence_sha256=candidate['evidence_sha256'],strategy_sha256=candidate['strategy_sha256'],
                dataset_sha256=candidate['dataset_sha256'],dataset_contents_verified=False,
                preregistration_verified=False,causal_novelty_proven=False)


def audit_temporal_separation(manifest):
    """Check declared information intervals only; read no market data.

    Intervals are half-open UTC epoch seconds and must include feature lookback,
    labels and trade exits, not just entry times. Registry completeness and the
    authenticity of registration timestamps require an external trusted record.
    This structural check cannot establish independent replication.
    """
    def result(reason=None):
        return dict(status='TEMPORAL_METADATA_REJECTED' if reason else 'TEMPORAL_METADATA_VERIFIED_NOT_ADMITTED',
                    reason=reason,interval_convention='HALF_OPEN_INFORMATION_SUPPORT_UTC_SECONDS',
                    dataset_contents_verified=False,registry_completeness_verified=False,
                    preregistration_verified=False,independent_replication_proven=False,
                    causal_novelty_proven=False,new_research_authorized=False,
                    orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
    def timestamp(x):
        return type(x) is int and 0 <= x <= 253402300799
    def interval(x):
        return isinstance(x,dict) and timestamp(x.get('start')) and timestamp(x.get('end')) and x['start']<x['end']
    if not isinstance(manifest,dict):return result('MALFORMED_MANIFEST')
    if manifest.get('interval_basis')!='FULL_INFORMATION_SUPPORT':
        return result('MISSING_INFORMATION_SUPPORT')
    for key in ('strategy_sha256','dataset_sha256'):
        value=manifest.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            return result('INVALID_'+key.upper())
    embargo=manifest.get('embargo_seconds')
    if type(embargo) is not int or not 0<=embargo<=31536000:
        return result('INVALID_EMBARGO')
    used=manifest.get('previously_used')
    holdout=manifest.get('reserved_holdout')
    replication=manifest.get('replication')
    if not isinstance(used,list) or not 1<=len(used)<=10000 or not all(interval(x) for x in used):
        return result('INVALID_PRIOR_INTERVALS')
    if not isinstance(holdout,list) or not 1<=len(holdout)<=10000 or not all(interval(x) for x in holdout):
        return result('INVALID_HOLDOUT_INTERVALS')
    if not interval(replication):return result('INVALID_REPLICATION_INTERVAL')
    registered=manifest.get('registered_at')
    first_access=manifest.get('first_replication_access_at')
    if not timestamp(registered) or not timestamp(first_access) or not registered<first_access:
        return result('REGISTRATION_NOT_BEFORE_ACCESS')
    if first_access<replication['end']:
        return result('ACCESS_BEFORE_COMPLETE_INTERVAL')
    if replication['start']<max(x['end'] for x in used)+embargo:
        return result('PRIOR_INFORMATION_OVERLAP_OR_EMBARGO')
    if any(replication['start']<x['end']+embargo and x['start']<replication['end']+embargo for x in holdout):
        return result('HOLDOUT_OVERLAP_OR_EMBARGO')
    return result()


def assess_replay_evidence(folds, settings, manifest):
    """Compose arithmetic, declared chronology and robustness on supplied trades.

    Returns are unlevered bps of raw entry notional, derived from checked R.
    Supplied stress_net_bps is ignored. Settings describe the supplied replay;
    neither stress calibration nor data provenance is authenticated here.
    No file access, execution or admission occurs.
    """
    import math
    from datetime import datetime, timezone
    safe=dict(causal_novelty_proven=False,independent_replication_proven=False,
              new_research_authorized=False,orders_allowed=False,mt5_allowed=False,
              holdout_allowed=False,auto_promotion_allowed=False)
    reports={}
    def result(status,reason=None):
        return dict(status=status,reason=reason,checks=reports,
                    unresolved=['DATASET_AND_STRATEGY_PROVENANCE','TRUSTED_PREREGISTRATION',
                                'HISTORICAL_USAGE_REGISTRY_COMPLETENESS','COST_STRESS_CALIBRATION',
                                'CAUSAL_NOVELTY_AND_INDEPENDENT_REPLICATION'],
                    return_basis='UNLEVERED_BPS_OF_RAW_ENTRY_NOTIONAL',**safe)
    temporal=audit_temporal_separation(manifest);reports['temporal']=temporal
    if temporal['status']!='TEMPORAL_METADATA_VERIFIED_NOT_ADMITTED':
        return result('REPLAY_EVIDENCE_REJECTED',temporal['reason'])
    if not isinstance(settings,dict):
        return result('REPLAY_EVIDENCE_REJECTED','MISSING_COST_SETTINGS')
    if not isinstance(folds,list) or len(folds)!=3 or any(not isinstance(x,list) or not x for x in folds):
        return result('REPLAY_EVIDENCE_REJECTED','THREE_NONEMPTY_FOLDS_REQUIRED')
    if sum(map(len,folds))>100000:
        return result('REPLAY_EVIDENCE_REJECTED','TRADE_BUDGET_EXCEEDED')
    costs=audit_replay_costs([t for f in folds for t in f],settings.get('fee_bps_per_side'),settings.get('slippage_bps_per_side'))
    reports['cost_arithmetic']=costs
    if costs['status']!='COST_ARITHMETIC_VERIFIED_NOT_ADMITTED':
        return result('REPLAY_EVIDENCE_REJECTED',costs['reason'])
    def epoch(value):
        if not isinstance(value,str):raise ValueError('TIMESTAMP_MUST_BE_ISO_STRING')
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.microsecond:
            raise ValueError('AWARE_WHOLE_SECOND_TIMESTAMP_REQUIRED')
        delta=parsed.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
        return delta.days*86400+delta.seconds
    normalized=[]
    window=manifest['replication']
    for fold in folds:
        rows=[]
        for trade in fold:
            try:entry,exit_=epoch(trade.get('entry_time')),epoch(trade.get('exit_time'))
            except (ValueError,TypeError,OverflowError):
                return result('REPLAY_EVIDENCE_REJECTED','INVALID_NATIVE_TIMESTAMPS')
            if not window['start']<=entry<exit_<window['end']:
                return result('REPLAY_EVIDENCE_REJECTED','TRADE_OUTSIDE_REPLICATION_INFORMATION_INTERVAL')
            # Relative price risk first avoids overflow from multiplying R by price.
            risk_fraction=abs(trade['raw_entry_price']-trade['stop_price'])/trade['raw_entry_price']
            bps=trade['net_r']*risk_fraction*10000
            if not math.isfinite(bps):
                return result('REPLAY_EVIDENCE_REJECTED','RETURN_CONVERSION_OVERFLOW')
            rows.append(dict(entry_time=entry,exit_time=exit_,stress_net_bps=bps))
        normalized.append(rows)
    robustness=assess_trade_robustness(normalized,manifest['strategy_sha256'])
    reports['robustness']=robustness
    if robustness['status']!='ROBUSTNESS_PASS_NOT_ADMITTED':
        return result('REPLAY_EVIDENCE_REJECTED',robustness.get('reason') or 'ROBUSTNESS_CRITERIA_FAILED')
    return result('REPLAY_CHECKS_PASS_SCIENTIFIC_REVIEW_BLOCKED')


def review_pending_replay():
    """Read one bounded request and evidence bundle; never confer trust or admission."""
    import os
    import stat
    safe=dict(new_research_authorized=False,orders_allowed=False,mt5_allowed=False,
              holdout_allowed=False,auto_promotion_allowed=False)
    def report(status,reason=None):
        return dict(status=status,reason=reason,**safe)
    def read(name,limit):
        if not isinstance(name,str) or not name.endswith('.json') or name.startswith('.') or '/' in name or '\\' in name:
            raise ValueError('INVALID_PATH')
        fd=os.open(S/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('NOT_REGULAR_FILE')
            raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('FILE_SIZE_LIMIT')
        doc=json.loads(raw)
        if not isinstance(doc,dict):raise ValueError('INVALID_SCHEMA')
        if any(doc.get(k) is not False for k in ('orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed')):
            raise ValueError('UNSAFE_FLAGS')
        return raw,doc
    request=S/'replay_review_request_v1.json'
    if not request.exists() and not request.is_symlink():
        return report('MISSING_REPLAY_EVIDENCE','NO_REVIEW_REQUEST')
    try:
        _,req=read(request.name,16384)
        if req.get('kind')!='V57_REPLAY_REVIEW_REQUEST_V1':raise ValueError('INVALID_REQUEST_KIND')
        raw,bundle=read(req.get('evidence_file'),2000000)
        digest=hashlib.sha256(raw).hexdigest()
        if req.get('evidence_sha256')!=digest:raise ValueError('EVIDENCE_HASH_MISMATCH')
        if bundle.get('kind')!='V57_REPLAY_REVIEW_BUNDLE_V1':raise ValueError('INVALID_BUNDLE_KIND')
        manifest=bundle.get('manifest')
        if not isinstance(manifest,dict):raise ValueError('MISSING_MANIFEST')
        for key in ('strategy_sha256','dataset_sha256'):
            if not isinstance(req.get(key),str) or req[key]!=manifest.get(key):
                raise ValueError('MANIFEST_BINDING_MISMATCH')
        evaluation=assess_replay_evidence(bundle.get('folds'),bundle.get('settings'),manifest)
        return dict(evaluation,evidence_sha256=digest,request_authenticity_verified=False)
    except (OSError,ValueError,TypeError,RecursionError) as error:
        return report('REPLAY_REVIEW_INPUT_REJECTED',str(error)[:160])

def main():
 p=S/"multimarket_evidence_registry_v3.json";h=hashlib.sha256(p.read_bytes()).hexdigest()
 cases=[({"new_causal_evidence_verified":True},"DENY_SELF_ATTESTED"),({"evidence_file":"arbitrary_pass.json"},"DENY_UNTRUSTED_SOURCE"),({"evidence_file":p.name,"evidence_sha256":"0"*64},"DENY_HASH"),({"evidence_file":p.name,"evidence_sha256":h},"INTEGRITY_AND_SCHEMA_VERIFIED_NOT_CAUSAL_NOVELTY")]
 if any(verify(x)!=expected for x,expected in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_INDEPENDENT_EVIDENCE_VERIFIER_V2","status":"PASS","tests":len(cases),"allowlisted_sources":list(ALLOW),"source_sha256":h,"source_schema_checked":True,"trade_robustness_evaluation_supported":True,"trade_cost_arithmetic_supported":True,"temporal_metadata_checks_supported":True,"composed_replay_review_supported":True,"causal_novelty_proven":False,"new_research_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 doc["replay_review"]=review_pending_replay()
 doc["stage03_initial_readiness"]=review_stage03_pending_initial()
 q=S/"independent_evidence_verifier_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"independent_evidence_verifier_v2.json")
 print("ALL PASS|INDEPENDENT_EVIDENCE_VERIFIER_V2|TESTS=4|ALLOWLIST=1|NOVELTY=NO")
def stage03_preexperiment_readiness(packet, sources, external_review_status):
    """Explain the next real science gap. This assessment NEVER authorizes execution.

    Inputs are treated as untrusted; callers must check source hashes separately.
    Signing a review is not evidence of a new causal mechanism or safe execution.
    """
    safe = dict(new_research_authorized=False, causal_novelty_proven=False,
                independent_replication_proven=False, orders_allowed=False,
                mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)
    def result(status, missing, tradeability=None):
        return dict(kind='OMEGA_STAGE03_PREEXPERIMENT_READINESS_V1', status=status,
                    missing_prerequisites=missing, external_review_status=external_review_status,
                    secondary_tradability_blockers=tradeability or [],
                    experiment_scope='NONTRADING_NEXT_300S_MIDQUOTE_FORECAST_ONLY',
                    development_experiment_authorized=False, **safe)
    if not isinstance(packet, dict) or not isinstance(sources, dict):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['INVALID_REVIEW_BUNDLE'])
    if (packet.get('kind') != 'OMEGA_STAGE03_EXTERNAL_PREEXPERIMENT_REVIEW_HANDOFF_V1'
            or packet.get('status') != 'READY_FOR_EXTERNAL_REVIEW_ONLY'
            or packet.get('instrument') != 'BINANCE_COINM_BTCUSD_PERP'
            or any(packet.get(k) is not False for k in (
                'development_authorized','candidate_admitted','search_executed',
                'backtest_executed','orders_allowed','mt5_allowed','holdout_allowed',
                'auto_promotion_allowed'))):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['UNSAFE_OR_INCOMPATIBLE_PACKET'])
    required={'protocol','review','regimes','temporal','costs','live','other_market','historical_quotes'}
    if set(sources)!=required or any(not isinstance(sources[k],dict) for k in required):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['INCOMPLETE_VERIFIED_EVIDENCE_SET'])
    protocol=sources['protocol']
    review=sources['review']
    regimes=sources['regimes']
    temporal=sources['temporal']
    live=sources['live']
    prices=sources['costs']
    quotes=sources['historical_quotes']
    # Local dossier flags and locally hashed samples are not independent attestations.
    # A signed eligibility-for-review letter is not an attestation of science.
    if any(packet.get(k) is True for k in (
            'scientific_novelty_verified',
            'independently_attested_future_preregistration',
            'reviewed_bounded_development_budget',
            'approved_information_timing_controls')):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['APPLICANT_SELF_ATTESTED_SCIENCE'])
    if (live.get('liquidation_event_payload_validated') is True
            or quotes.get('quotes_are_proven_received_at_decision_time') is True):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['LOCAL_FEED_ATTESTATION_NOT_INDEPENDENT'])
    if (protocol.get('kind')!='V57_PROSPECTIVE_CAUSAL_PROTOCOL_V1'
            or protocol.get('hypothesis_status')!='FORMULATED_FOR_REVIEW'
            or review.get('status')!='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'
            or regimes.get('instrument')!='BINANCE_COINM_BTCUSD_PERP'
            or temporal.get('target')!='BTCUSD_PERP'
            or prices.get('symbol')!='BTCUSD_PERP'
            or quotes.get('instrument')!='BINANCE_COINM_BTCUSD_PERP'
            or live.get('kind')!='OMEGA_STAGE03_COINM_WS_BOUNDED_ONE_SHOT_OBSERVATION_V1'):
        return result('PREEXPERIMENT_INPUT_REJECTED', ['INCOMPATIBLE_EVIDENCE_SCHEMA_OR_INSTRUMENT'])
    missing=[]
    signed_rejections = {
        'SIGNED_INITIAL_REVIEW_REJECT_REDUNDANT_MECHANISM_NOT_AUTHORIZED',
        'SIGNED_INITIAL_REVIEW_REJECT_INSUFFICIENT_SOURCE_NOT_AUTHORIZED',
    }
    if external_review_status in signed_rejections:
        return result('PREEXPERIMENT_REJECTED_BY_INDEPENDENT_REVIEW',
                      [external_review_status])
    if external_review_status=='SIGNED_INITIAL_REVIEW_REQUEST_FIXED_DEFINITION_NOT_AUTHORIZED':
        return result('PREEXPERIMENT_REVISION_REQUESTED_BY_INDEPENDENT_REVIEW',
                      [external_review_status])
    if external_review_status!='INITIAL_REVIEW_SIGNATURE_VERIFIED_NOT_AUTHORIZED':
        missing.append('EXTERNAL_INDEPENDENT_REVIEW_SIGNATURE_AND_TRUSTED_KEY')
    if packet.get('scientific_novelty_verified') is not True:
        missing.append('INDEPENDENT_MECHANISTIC_NOVELTY_VS_EXHAUSTED_FAMILIES')
    # Exchange historical event time does not prove information was received
    # early enough at the actual intended decision timestamp.
    if live.get('liquidation_event_payload_validated') is not True or live.get('new_probe_events_received',0)<=0:
        missing.append('TARGET_COINM_LIVE_FORCEORDER_RECEIPT_AND_GAP_PROVENANCE')
    if quotes.get('quotes_are_proven_received_at_decision_time') is not True:
        missing.append('REALTIME_BOOK_AND_LIQUIDATION_INFORMATION_CHRONOLOGY')
    # The first nontrading experiment measures quote displacement, not P&L.
    # Do not demand live broker fills before even observing the hypothesis.
    # Real costs remain mandatory before ANY tradable/PF interpretation.
    tradeability=[]
    if (prices.get('reference_regular_fee_schedule',{}).get('account_fee_tier_verified') is not True
            or quotes.get('broker_fills_verified') is not True):
        tradeability.append('VENUE_ACCOUNT_COSTS_AND_EXECUTABLE_FILL_SEMANTICS')
    if packet.get('independently_attested_future_preregistration') is not True:
        missing.append('INDEPENDENTLY_ATTESTED_FUTURE_PREREGISTRATION')
    if packet.get('reviewed_bounded_development_budget') is not True:
        missing.append('INDEPENDENTLY_REVIEWED_BOUNDED_DEVELOPMENT_BUDGET')
    if packet.get('approved_information_timing_controls') is not True:
        missing.append('FALSIFIABLE_INFORMATION_TIMING_AND_CONTROL_DESIGN_REVIEW')
    # A machine-readable checklist is evidence assessment, not permission.
    return result('PREEXPERIMENT_SCIENCE_BLOCKED' if missing else
                  'PREEXPERIMENT_EVIDENCE_COMPLETE_REQUIRES_SEPARATE_PERMISSION',
                  missing,tradeability)


def review_stage03_pending_initial():
    """Verify packet digests then report blockers; no authority to start search."""
    import runpy
    folder=S/'stage03_liquidation_source_access_v1'
    packet_path=folder/'initial_method_review_handoff_v1.json'
    try:
        if packet_path.is_symlink() or not packet_path.is_file() or packet_path.stat().st_size>32768:
            raise ValueError('INVALID_PACKET_PATH')
        packet=json.loads(packet_path.read_bytes())
        if not isinstance(packet,dict):
            raise ValueError('INVALID_PACKET')
        refs=packet.get('verified_source_files')
        required={'protocol','review','regimes','temporal','costs','live','other_market','historical_quotes'}
        if not isinstance(refs,dict) or set(refs)!=required:
            raise ValueError('INVALID_MANIFEST')
        docs={}
        for key in required:
            ref=refs[key]
            if not isinstance(ref,dict) or set(ref)!= {'relative_file','sha256'}:
                raise ValueError('INVALID_SOURCE_REFERENCE')
            name=ref['relative_file']
            if not isinstance(name,str):
                raise ValueError('INVALID_SOURCE_PATH')
            parts=Path(name).parts
            if not parts or parts[0]!='stage03_liquidation_source_access_v1' or '..' in parts:
                raise ValueError('INVALID_SOURCE_PATH')
            path=S.joinpath(*parts)
            if path.is_symlink() or not path.is_file() or path.stat().st_size>50000:
                raise ValueError('INVALID_SOURCE_FILE')
            blob=path.read_bytes()
            expected=ref['sha256']
            if not isinstance(expected,str) or len(expected)!=64 or hashlib.sha256(blob).hexdigest()!=expected:
                raise ValueError('HASH_MISMATCH')
            docs[key]=json.loads(blob)
        ns=runpy.run_path(str(Path(__file__).with_name('v57_prospective_causal_protocol_v1.py')))
        reviewer=ns['verify_signed_initial_review'](
            packet_path,folder/'external_initial_review_v1.json',
            folder/'external_initial_review_v1.sig',
            Path('/etc/tradingai/omega-scientific-review-pubkey.pem'))
        return stage03_preexperiment_readiness(packet,docs,reviewer['status'])
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,AttributeError):
        return stage03_preexperiment_readiness(None,None,'DENY_EVIDENCE_NOT_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STOP|FAIL|INDEPENDENT_EVIDENCE_VERIFIER_V2|'+str(e))
        sys.exit(3)
