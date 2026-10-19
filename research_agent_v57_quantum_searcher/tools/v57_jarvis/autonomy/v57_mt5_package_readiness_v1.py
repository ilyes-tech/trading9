#!/usr/bin/env python3
"""Read-only MT5 packaging readiness gate. No package generation or execution."""
import hashlib,json,sys,time,os,stat,subprocess,tempfile
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
def load(p):
 if p.is_symlink() or not p.is_file():return None
 return json.loads(p.read_text())
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"))
# An externally provisioned, ROOT-owned trust anchor; never generate it
# inside the project. A signature can certify a review packet's integrity
# and reviewer identity but does not independently prove broker fills.
BROKER_COST_REVIEW_TRUST_KEY=Path('/etc/tradingai/omega-mt5-broker-cost-pubkey.pem')


def _small_regular_bytes(path, limit, require_root_protected=False):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_size>limit
                or (require_root_protected and
                    (info.st_uid!=0 or info.st_mode & 0o022))):
            raise ValueError('UNTRUSTED_OR_OVERSIZED_ATTESTATION_FILE')
        data=os.read(fd,limit+1)
        if len(data)>limit or len(data)!=info.st_size:
            raise ValueError('INVALID_ATTESTATION_FILE_SIZE')
        return data
    finally:
        os.close(fd)


def signed_broker_cost_review_valid(cost_path, signature_path, trust_key_path, expected_cost=None):
    """Only a preprovisioned trusted Ed25519 signer can attest cost packet.

    The detached signature covers EXACT bytes of the broker cost binding JSON
    whose export hash, account/server match and fee component claims are
    checked separately. Trust-key creation must be external to JARVIS.
    This grants review eligibility prerequisite only, NEVER trading access.
    """
    try:
        raw=_small_regular_bytes(cost_path,65536)
        detached=_small_regular_bytes(signature_path,256)
        trusted=_small_regular_bytes(trust_key_path,8192,require_root_protected=True)
        if len(detached)!=64 or not trusted.startswith(b'-----BEGIN PUBLIC KEY-----'):
            return False
        body=json.loads(raw)
        if not isinstance(body,dict) or (expected_cost is not None and body!=expected_cost):
            return False
        # Verify the immutable byte snapshots, not mutable original paths.
        # Otherwise the JSON could be swapped after comparison to expected_cost.
        with tempfile.TemporaryDirectory(prefix='omega_broker_review_') as temp:
            private=Path(temp)
            source=private/'cost.json'
            sig=private/'cost.sig'
            key=private/'review_pubkey.pem'
            source.write_bytes(raw)
            sig.write_bytes(detached)
            key.write_bytes(trusted)
            os.chmod(key,0o600)
            pub=subprocess.run(['openssl','pkey','-pubin','-in',str(key),
                                '-text','-noout'],capture_output=True,text=True,timeout=8)
            if pub.returncode!=0 or 'ED25519 Public-Key:' not in pub.stdout:
                return False
            verified=subprocess.run(['openssl','pkeyutl','-verify','-pubin',
                                     '-inkey',str(key),'-sigfile',str(sig),
                                     '-rawin','-in',str(source)],
                                    capture_output=True,timeout=8)
            return verified.returncode==0
    except (OSError,ValueError,TypeError,subprocess.SubprocessError,
            json.JSONDecodeError):
        return False


def broker_cost_blockers(connection, archived_spread, cost_binding, source_export, source_authenticity_verified=False):
    """Separate broker-account execution evidence from old historical MT5 spreads.

    This adds a packaging-REVIEW prerequisite; it cannot authorize orders.
    The future cost binding must refer to the very same read-only broker account,
    and raw exported evidence must be SHA256-bound, not a bare status toggle.
    """
    reasons=[]
    connected=(isinstance(connection,dict)
        and connection.get("status")=="VERIFIED_READONLY_DEMO_BROKER_ACCOUNT"
        and connection.get("account_specific_broker_authenticated") is True
        and connection.get("broker_server_selected") is True
        and isinstance(connection.get("server"),str) and bool(connection["server"])
        and isinstance(connection.get("account_ref_hash"),str)
        and len(connection["account_ref_hash"])==64)
    if not connected:
        reasons.append("MT5_DEMO_BROKER_CONNECTION_UNVERIFIED")
    # March MT5 archive is a useful reference, not proof of current account costs.
    if (not isinstance(archived_spread,dict)
            or archived_spread.get("status")!="PASS_ARCHIVED_DEV_SPREAD_PROVENANCE_ONLY_BROKER_COST_BINDING_INCOMPLETE"
            or archived_spread.get("scientific_admission") is not False
            or archived_spread.get("orders_allowed") is not False
            or archived_spread.get("holdout_read") is not False):
        reasons.append("ARCHIVED_SPREAD_PROVENANCE_UNVERIFIED")
    valid=(connected and isinstance(cost_binding,dict)
        and cost_binding.get("status")=="BROKER_ACCOUNT_COST_INPUTS_VERIFIED_FOR_REVIEW_ONLY"
        and cost_binding.get("kind")=="OMEGA_MT5_BROKER_COST_INPUT_BINDING_V1"
        and cost_binding.get("server")==connection["server"]
        and cost_binding.get("account_ref_hash")==connection["account_ref_hash"]
        and cost_binding.get("commission_for_account_verified") is True
        and cost_binding.get("bid_ask_spread_for_account_verified") is True
        and cost_binding.get("swap_for_account_verified") is True
        and cost_binding.get("fill_policy_for_account_verified") is True
        and cost_binding.get("orders_allowed") is False
        and cost_binding.get("scientific_admission") is False
        and cost_binding.get("holdout_read") is False
        and isinstance(source_export,dict)
        and source_export.get("kind")=="OMEGA_MT5_READONLY_ACCOUNT_COST_EXPORT_V1"
        and source_export.get("read_only") is True
        and source_export.get("orders_sent") is False
        and source_export.get("server")==connection["server"]
        and source_export.get("account_ref_hash")==connection["account_ref_hash"]
        and cost_binding.get("source_export_sha256")==hashlib.sha256(canon(source_export).encode()).hexdigest())
    # A matching hash is *not* evidence of source authenticity. The source
    # binding may be accepted for REVIEW only after verifying a DETACHED
    # Ed25519 signature under the independently controlled trust key.
    if not valid:
        reasons.append("MT5_EXECUTABLE_BROKER_COST_AND_FILL_AUTHORITY_NOT_PROVISIONED")
    if not (valid and source_authenticity_verified is True):
        reasons.append("MT5_BROKER_COST_SOURCE_AUTHENTICITY_NOT_VERIFIED")
    return reasons

def main():
 d=load(S/"phase2_deep_validation_v1.json")
 result=load(S/"phase2_scientific_result_v1.json")
 costs=load(S/"stage03_mt5_broker_cost_input_binding_v1.json")
 signature_verified=signed_broker_cost_review_valid(
  S/"stage03_mt5_broker_cost_input_binding_v1.json",
  S/"stage03_mt5_broker_cost_input_binding_v1.sig",
  BROKER_COST_REVIEW_TRUST_KEY,costs)
 reasons=broker_cost_blockers(load(S/"stage03_mt5_demo_connection_readonly_precheck_v1.json"),load(S/"stage03_mt5_march_development_spread_preflight_v1.json"),costs,load(S/"stage03_mt5_readonly_account_cost_export_v1.json"),source_authenticity_verified=signature_verified)
 sid=d.get("strategy_id") if d else None
 if not d or d.get("status")!="COMPLETED" or (d.get("deep") or {}).get("status")!="DEEP_PASS" or d.get("independent_replay_exact_pass") is not True:reasons.append("DEEP_PASS_MISSING")
 if not result or not d or result.get("execution_token")!=d.get("execution_token"):reasons.append("SCIENTIFIC_BINDING_MISSING")
 token=(result or {}).get("execution_token")
 gate=load(S/"search_execution_gate_v1.json")
 ledger=load(S/"search_execution_ledger_v1.json")
 scientific_ledger=load(S/"phase2_scientific_execution_ledger_v1.json")
 if not isinstance(token,str) or len(token)!=64 or not gate or gate.get("ready") is not True or gate.get("execution_token")!=token or not ledger or (ledger.get("consumed_tokens") or []).count(token)!=1 or not scientific_ledger or (scientific_ledger.get("completed_tokens") or []).count(token)!=1:reasons.append("SCIENTIFIC_EXECUTION_PROVENANCE_MISSING")
 triage=load(S/"phase2_result_triage_v1.json")
 promotion=load(S/"phase2_promotion_decision_v1.json")
 if not triage or triage.get("execution_token")!=(d or {}).get("execution_token") or triage.get("decision")!="VALIDATION_REQUIRED" or triage.get("deep_validation_allowed") is not True:reasons.append("TRIAGE_BINDING_MISSING")
 if not promotion or promotion.get("execution_token")!=(d or {}).get("execution_token") or promotion.get("strategy_id")!=sid or promotion.get("decision")!="REVIEW_ELIGIBLE" or promotion.get("promotion_executed") is not False:reasons.append("PROMOTION_REVIEW_MISSING")
 if not result or result.get("status")!="COMPLETED_RESEARCH_ONLY" or result.get("independent_validation_required") is not True or result.get("pool_mutation_allowed") is not False or any(result.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):reasons.append("SCIENTIFIC_SAFETY_MISSING")
 if d and any(d.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):reasons.append("DEEP_SAFETY_MISSING")
 if not isinstance(sid,str) or len(sid)!=64:reasons.append("STRATEGY_ID_MISSING")
 proof=None
 if not reasons:
  records=(result.get("result") or {}).get("records") or []
  matches=[x for x in records if (x.get("strategy") or {}).get("strategy_id")==sid and (x.get("result") or {}).get("exact_pass") is True]
  if len(matches)!=1:reasons.append("EXACT_STRATEGY_NOT_UNIQUE")
  else:
   strategy=matches[0]["strategy"]
   proof=load(R/"work/deployment_fidelity_v1/proofs"/(sid+".json"))
   if not proof:reasons.append("FIDELITY_PROOF_MISSING")
   else:
    h=proof.get("proof_sha256");body=dict(proof);body.pop("proof_sha256",None)
    if hashlib.sha256(canon(body).encode()).hexdigest()!=h:reasons.append("PROOF_HASH_INVALID")
    if proof.get("strategy_sha256")!=hashlib.sha256(canon(strategy).encode()).hexdigest() or proof.get("strategy_id")!=sid:reasons.append("STRATEGY_PROOF_MISMATCH")
    v=proof.get("verdict") or {};integrity=v.get("research_integrity") or {}
    if proof.get("promotion_allowed") is not True or v.get("conclusion")!="DEPLOYMENT_VERIFIED":reasons.append("FIDELITY_NOT_VERIFIED")
    if any(integrity.get(k) is not False for k in ("holdout_read","orders_allowed","september_2026_data_accessed")):reasons.append("FIDELITY_INTEGRITY_UNPROVEN")
 status="REVIEW_ELIGIBLE" if not reasons else "BLOCKED"
 out={"kind":"JARVIS_MT5_PACKAGE_READINESS_V1","status":status,"strategy_id":sid,"reasons":reasons,"checked_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"package_generated":False,"human_approval_required":True,"orders_allowed":False,"mt5_allowed":False,"auto_promotion_allowed":False}
 p=S/"mt5_package_readiness_v1.tmp";p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");p.replace(S/"mt5_package_readiness_v1.json")
 print("ALL PASS|MT5_PACKAGE_READINESS|"+status+"|PACKAGE=NO|ORDERS=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("STOP|FAIL|MT5_PACKAGE_READINESS|"+type(e).__name__+":"+str(e));sys.exit(3)
