import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
REVIEW_TRUST_KEY=Path('/etc/tradingai/omega-scientific-review-pubkey.pem')


def verify_external_review_signature(candidate, candidate_sha256):
    """Externally signed review eligibility, never scientific admission.

    Trust key is separately provisioned outside the repository/state, root-owned
    and immutable to the research account. The review binds all three proofs.
    Missing authority, invalid signature, or stale evidence must fail closed.
    """
    import os
    import stat
    import subprocess
    import tempfile

    def read_regular(path, max_bytes, trusted=False):
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode):raise ValueError('NOT_REGULAR_FILE')
            if trusted and (info.st_uid!=0 or info.st_mode & 0o022):
                raise ValueError('UNTRUSTED_PUBLIC_KEY_PERMISSIONS')
            payload=f.read(max_bytes+1)
        if len(payload)>max_bytes:raise ValueError('SIZE_LIMIT')
        return payload

    if not isinstance(candidate_sha256,str) or len(candidate_sha256)!=64:
        return 'DENY_CANDIDATE_HASH'
    try:
        public_key=read_regular(REVIEW_TRUST_KEY,4096,trusted=True)
    except (OSError,ValueError):
        return 'DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED'
    try:
        review=read_regular(S/'causal_independent_review_v1.json',16384)
        signature=read_regular(S/'causal_independent_review_v1.sig',256)
        payload=json.loads(review)
        if not isinstance(payload,dict):return 'DENY_EXTERNAL_REVIEW_SCHEMA'
        expected={'kind':'OMEGA_EXTERNAL_SCIENTIFIC_REVIEW_V1',
                  'candidate_sha256':candidate_sha256,
                  'family':candidate.get('native_family'),
                  'market':candidate.get('market'),
                  'source_sha256':candidate.get('source_sha256'),
                  'novelty_evidence_sha256':candidate.get('novelty_evidence_sha256'),
                  'independent_replication_sha256':candidate.get('independent_replication_sha256'),
                  'decision':'ELIGIBLE_FOR_INDEPENDENT_SCIENTIFIC_REVIEW_ONLY'}
        if any(payload.get(k)!=v for k,v in expected.items()):
            return 'DENY_EXTERNAL_REVIEW_BINDING'
        if not isinstance(payload.get('reviewer_id'),str) or not payload['reviewer_id'].strip():
            return 'DENY_EXTERNAL_REVIEW_SCHEMA'
        with tempfile.TemporaryDirectory(prefix='omega-external-review-') as folder:
            folder=Path(folder)
            key_file,review_file,sig_file=(folder/x for x in ('public.pem','review.json','review.sig'))
            key_file.write_bytes(public_key)
            review_file.write_bytes(review)
            sig_file.write_bytes(signature)
            key_check=subprocess.run(('/usr/bin/openssl','pkey','-pubin',
                                      '-in',str(key_file),'-text_pub','-noout'),
                                     capture_output=True,timeout=6,check=False)
            if key_check.returncode!=0 or b'ED25519 Public-Key' not in key_check.stdout:
                return 'DENY_EXTERNAL_REVIEW_KEY_NOT_ED25519'
            check=subprocess.run(('/usr/bin/openssl','pkeyutl','-verify','-pubin',
                                  '-inkey',str(key_file),'-sigfile',str(sig_file),
                                  '-rawin','-in',str(review_file)),capture_output=True,
                                 timeout=6,check=False)
        if check.returncode!=0:return 'DENY_EXTERNAL_REVIEW_SIGNATURE_INVALID'
        return 'TRUSTED_EXTERNAL_REVIEW_SIGNATURE_VERIFIED_NOT_ADMISSION'
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired):
        return 'DENY_EXTERNAL_REVIEW_UNREADABLE'
def check(x,exhausted):
 if not isinstance(x,dict):return "DENY_MALFORMED"
 family=x.get("native_family")
 if not isinstance(family,str) or not family.strip():return "DENY_MISSING_FAMILY"
 if family in exhausted:return "DENY_EXHAUSTED_FAMILY"
 if any(x.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE"
 if x.get("new_causal_evidence_verified") is True:return "DENY_UNTRUSTED_SELF_ATTESTATION"
 return "DENY_NO_INDEPENDENT_EVIDENCE_VERIFIER"

def review_submitted_candidate(coverage, registry):
    """Inspect a real dossier for review eligibility, never scientific admission."""
    import importlib.util
    import os
    import stat
    flags=dict(new_family_admitted=False,research_execution_authorized=False,
               orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
    def result(decision,reason,**extra):
        return dict(decision=decision,reason=reason,**flags,**extra)
    def read(path,limit):
        fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('NOT_REGULAR_FILE')
            raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('FILE_SIZE_LIMIT')
        doc=json.loads(raw)
        if not isinstance(doc,dict):raise ValueError('INVALID_SCHEMA')
        return raw,doc
    def module(name):
        spec=importlib.util.spec_from_file_location('_omega_'+name,Path(__file__).with_name(name+'.py'))
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    path=S/'causal_family_candidate_v2.json'
    if not path.exists() and not path.is_symlink():
        return result('MISSING','NO_CANDIDATE_SUBMITTED')
    try:
        raw,candidate=read(path,16384)
        digest=hashlib.sha256(raw).hexdigest()
        if candidate.get('kind')!='V57_CAUSAL_FAMILY_CANDIDATE_V2':
            return result('REJECT','INVALID_CANDIDATE_KIND',candidate_sha256=digest)
        if not isinstance(coverage,dict) or not isinstance(registry,dict):
            return result('REJECT','INVALID_REFERENCE_INPUTS')
        if coverage.get('kind')!='V57_NATIVE_CAPABILITY_COVERAGE_V2' or coverage.get('status')!='PASS' or registry.get('kind')!='V57_MULTIMARKET_EVIDENCE_REGISTRY_V3' or registry.get('status')!='PASS':
            return result('REJECT','INVALID_REFERENCE_INPUTS')
        if not isinstance(coverage.get('native_families'),list) or not isinstance(coverage.get('exhausted_families'),list) or not isinstance(registry.get('markets'),dict):
            return result('REJECT','INVALID_REFERENCE_SCHEMA')
        intake=module('v57_causal_evidence_intake_v1')
        decision=intake.assess(candidate,coverage,registry)
        if decision!='PENDING_INDEPENDENT_REPLICATION_REVIEW_NOT_AUTHORIZED':
            return result('REJECT',decision,candidate_sha256=digest)
        # Read each evidence once, with independent size and hash checks.
        evidence={}
        declared_missing=[]
        mapping=(('source_file','source_sha256',None),
                 ('novelty_file','novelty_evidence_sha256','V57_CAUSAL_NOVELTY_EVIDENCE'),
                 ('replication_file','independent_replication_sha256','V57_CAUSAL_REPLICATION_EVIDENCE'))
        names=[]
        for field,hash_field,kind in mapping:
            name=candidate.get(field)
            if not isinstance(name,str) or not name.endswith('.json') or name.startswith('.') or '/' in name or '\\' in name:
                return result('REJECT','INVALID_EVIDENCE_PATH',candidate_sha256=digest)
            names.append(name)
            body,doc=read(S/name,2000000)
            if hashlib.sha256(body).hexdigest()!=candidate[hash_field]:
                return result('REJECT','EVIDENCE_HASH_MISMATCH',candidate_sha256=digest)
            if any(doc.get(k) is not False for k in ('orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed')):
                return result('REJECT','UNSAFE_EVIDENCE',candidate_sha256=digest)
            if kind is not None and doc.get('kind')!=kind:
                return result('REJECT','EVIDENCE_KIND_MISMATCH',candidate_sha256=digest)
            if doc.get('family')!=candidate['native_family'] or doc.get('market')!=candidate['market']:
                return result('REJECT','EVIDENCE_IDENTITY_MISMATCH',candidate_sha256=digest)
            evidence[field]=dict(file=name,sha256=candidate[hash_field])
            # A signed-looking digest does not overrule evidence explicitly
            # declaring that scientific authenticity or replication is absent.
            required_by_file={
                'source_file':('source_authenticity_independently_verified',
                               'market_registry_instrument_identical_verified'),
                'novelty_file':('mechanistic_novelty_independently_verified',),
                'replication_file':('independent_experiment_replication_proven',),
            }
            # Absence, non-bool and explicit denial all fail closed. True
            # remains an untrusted claim: only REVIEW_REQUIRED, never admission.
            declared_missing.extend(field+'.'+key for key in required_by_file[field]
                                    if doc.get(key) is not True)
        if len(set(names))!=3:
            return result('REJECT','IDENTICAL_EVIDENCE_FILES',candidate_sha256=digest)
        if declared_missing:
            return result('REJECT','EXPLICIT_REQUIRED_SCIENTIFIC_EVIDENCE_MISSING',
                          candidate_sha256=digest,missing_prerequisites=declared_missing,
                          source_authenticity_verified=False,independence_proven=False,
                          causal_novelty_proven=False)
        attestation=verify_external_review_signature(candidate,digest)
        if attestation!='TRUSTED_EXTERNAL_REVIEW_SIGNATURE_VERIFIED_NOT_ADMISSION':
            return result('REJECT',attestation,candidate_sha256=digest,
                          source_authenticity_verified=False,independence_proven=False,
                          causal_novelty_proven=False)
        return result('REVIEW_REQUIRED','EXTERNALLY_SIGNED_FILES_VERIFIED_SCIENTIFIC_REVIEW_PENDING',
                      candidate_sha256=digest,native_family=candidate['native_family'],market=candidate['market'],
                      evidence=evidence,source_authenticity_verified=False,independence_proven=False,
                      causal_novelty_proven=False)
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        return result('REJECT','UNREADABLE_OR_INVALID_DOSSIER',detail=str(error)[:160])

def technical_verifier_status():
    """Check that the existing mechanical verifier was run and bound to the registry.

    This is an engineering-integrity check, never a scientific attestation.
    """
    registry = S / "multimarket_evidence_registry_v3.json"
    artifact = S / "independent_evidence_verifier_v2.json"
    try:
        if any(p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= 50000
               for p in (registry, artifact)):
            return "TECHNICAL_VERIFIER_NOT_VERIFIED"
        evidence = json.loads(artifact.read_bytes())
        readiness = evidence.get("stage03_initial_readiness")
        required = ("trade_robustness_evaluation_supported", "trade_cost_arithmetic_supported",
                    "temporal_metadata_checks_supported", "composed_replay_review_supported",
                    "source_schema_checked")
        safe = ("orders_allowed", "mt5_allowed", "holdout_allowed", "auto_promotion_allowed",
                "new_research_authorized", "causal_novelty_proven")
        if (not isinstance(readiness, dict)
                or readiness.get("kind") != "OMEGA_STAGE03_PREEXPERIMENT_READINESS_V1"
                or readiness.get("development_experiment_authorized") is not False
                or any(readiness.get(k) is not False for k in
                       ("orders_allowed", "mt5_allowed", "holdout_allowed", "auto_promotion_allowed",
                        "new_research_authorized", "causal_novelty_proven"))
                or evidence.get("kind") != "V57_INDEPENDENT_EVIDENCE_VERIFIER_V2"
                or evidence.get("status") != "PASS"
                or evidence.get("source_sha256") != hashlib.sha256(registry.read_bytes()).hexdigest()
                or any(evidence.get(k) is not True for k in required)
                or any(evidence.get(k) is not False for k in safe)):
            return "TECHNICAL_VERIFIER_NOT_VERIFIED"
        return "TECHNICAL_VERIFIER_CONNECTED_NOT_SCIENTIFIC_ADMISSION"
    except (OSError, ValueError, TypeError, AttributeError):
        return "TECHNICAL_VERIFIER_NOT_VERIFIED"


def main():
 p=S/"native_capability_coverage_v2.json";v=json.loads(p.read_text())
 if v.get("kind")!="V57_NATIVE_CAPABILITY_COVERAGE_V2" or v.get("status")!="PASS" or len(v.get("exhausted_families",[]))!=5:raise RuntimeError("COVERAGE")
 exhausted=set(v["exhausted_families"]);safe={k:False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")}
 cases=[({}, "DENY_MISSING_FAMILY"),({"native_family":"momentum",**safe},"DENY_EXHAUSTED_FAMILY"),({"native_family":"new_family","new_causal_evidence_verified":True,**safe},"DENY_UNTRUSTED_SELF_ATTESTATION"),({"native_family":"new_family",**safe},"DENY_NO_INDEPENDENT_EVIDENCE_VERIFIER"),({"native_family":"new_family","orders_allowed":True,**{k:v for k,v in safe.items() if k!="orders_allowed"}},"DENY_UNSAFE")]
 if any(check(x,exhausted)!=expected for x,expected in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_CAUSAL_FAMILY_ADMISSION_V2","status":"PASS","coverage_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"tests":len(cases),"independent_evidence_verifier":technical_verifier_status(),"scientific_independent_admission":"NOT_ESTABLISHED","external_signed_review_gate":"ED25519_IMPLEMENTED_FAIL_CLOSED_NOT_SCIENTIFIC_ADMISSION","self_attestation_accepted":False,"new_family_admitted":False,"research_execution_authorized":False,**safe}
 registry=json.loads((S/"multimarket_evidence_registry_v3.json").read_text())
 doc["candidate_review"]=review_submitted_candidate(v,registry)
 q=S/"causal_family_admission_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"causal_family_admission_v2.json")
 print("ALL PASS|CAUSAL_FAMILY_ADMISSION_V2|TESTS=5|SELF_ATTESTATION=DENIED|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|CAUSAL_FAMILY_ADMISSION_V2|"+str(e));sys.exit(3)
