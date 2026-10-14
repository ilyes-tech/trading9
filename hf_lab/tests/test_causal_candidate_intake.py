"""Actual candidate intake on synthetic dossiers; never grants admission."""
import hashlib,json,os,runpy,subprocess
from pathlib import Path
import pytest
ROOT=Path('/home/trading/TradingAI-HF-Lab')
A=ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy'
NS=runpy.run_path(os.environ.get('OMEGA_CAUSAL_ADMISSION',str(A/'v57_causal_family_admission_v2.py')))
SAFE=dict(orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
C=dict(kind='V57_NATIVE_CAPABILITY_COVERAGE_V2',status='PASS',native_families=['trend'],exhausted_families=['trend'])
R=dict(kind='V57_MULTIMARKET_EVIDENCE_REGISTRY_V3',status='PASS',markets={'BTCUSD':{}})
@pytest.fixture
def review(tmp_path):
 f=NS['review_submitted_candidate'];f.__globals__['S']=tmp_path
 return f,tmp_path
def dossier(p):
 x=dict(kind='V57_CAUSAL_FAMILY_CANDIDATE_V2',native_family='SYNTHETIC_NEW',market='BTCUSD',**SAFE)
 for field,h,kind in [('source_file','source_sha256','SYNTHETIC_SOURCE'),('novelty_file','novelty_evidence_sha256','V57_CAUSAL_NOVELTY_EVIDENCE'),('replication_file','independent_replication_sha256','V57_CAUSAL_REPLICATION_EVIDENCE')]:
  body=json.dumps(dict(kind=kind,family=x['native_family'],market=x['market'],**SAFE)).encode()
  name=field+'.json';(p/name).write_bytes(body);x[field]=name;x[h]=hashlib.sha256(body).hexdigest()
 save(p,x);return x
def save(p,x):(p/'causal_family_candidate_v2.json').write_text(json.dumps(x))
REQUIRED=[('source_file','source_sha256','source_authenticity_independently_verified'),
          ('source_file','source_sha256','market_registry_instrument_identical_verified'),
          ('novelty_file','novelty_evidence_sha256','mechanistic_novelty_independently_verified'),
          ('replication_file','independent_replication_sha256','independent_experiment_replication_proven')]
def assert_claims_for_review(p,x):
 for field,h,flag in REQUIRED:
  path=p/x[field];doc=json.loads(path.read_text());doc[flag]=True
  body=json.dumps(doc).encode();path.write_bytes(body)
  x[h]=hashlib.sha256(body).hexdigest()
 save(p,x)
def test_missing_distinguished_from_invalid(review):
 f,p=review;assert f(C,R)['decision']=='MISSING'
 (p/'causal_family_candidate_v2.json').write_text('[]')
 assert f(C,R)['decision']=='REJECT'
def test_verified_claims_without_independent_authority_are_rejected(review):
 f,p=review;x=dossier(p);assert_claims_for_review(p,x);out=f(C,R)
 assert out['decision']=='REJECT'
 assert out['reason']=='DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED'
 for k in ('new_family_admitted','research_execution_authorized','causal_novelty_proven','independence_proven','source_authenticity_verified'):
  assert out[k] is False

def test_external_ed25519_signature_binds_review_without_admission(review):
 f,p=review;x=dossier(p);assert_claims_for_review(p,x)
 private=p/'temporary-test-only-private.pem';public=p/'trusted-test-only-public.pem'
 subprocess.run(['/usr/bin/openssl','genpkey','-algorithm','ED25519','-out',str(private)],check=True,capture_output=True)
 subprocess.run(['/usr/bin/openssl','pkey','-in',str(private),'-pubout','-out',str(public)],check=True,capture_output=True)
 public.chmod(0o644);f.__globals__['REVIEW_TRUST_KEY']=public
 candidate_hash=hashlib.sha256((p/'causal_family_candidate_v2.json').read_bytes()).hexdigest()
 payload=dict(kind='OMEGA_EXTERNAL_SCIENTIFIC_REVIEW_V1',candidate_sha256=candidate_hash,
              family=x['native_family'],market=x['market'],source_sha256=x['source_sha256'],
              novelty_evidence_sha256=x['novelty_evidence_sha256'],
              independent_replication_sha256=x['independent_replication_sha256'],
              decision='ELIGIBLE_FOR_INDEPENDENT_SCIENTIFIC_REVIEW_ONLY',reviewer_id='INDEPENDENT_TEST_FIXTURE')
 review_file=p/'causal_independent_review_v1.json';review_file.write_text(json.dumps(payload,sort_keys=True))
 signature=p/'causal_independent_review_v1.sig'
 subprocess.run(['/usr/bin/openssl','pkeyutl','-sign','-inkey',str(private),'-rawin',
                 '-in',str(review_file),'-out',str(signature)],check=True,capture_output=True)
 out=f(C,R)
 assert out['decision']=='REVIEW_REQUIRED' and out['reason']=='EXTERNALLY_SIGNED_FILES_VERIFIED_SCIENTIFIC_REVIEW_PENDING'
 for key in ('new_family_admitted','research_execution_authorized','causal_novelty_proven','independence_proven','source_authenticity_verified','orders_allowed','mt5_allowed'):
  assert out[key] is False
 payload['reviewer_id']='TAMPERED';review_file.write_text(json.dumps(payload,sort_keys=True))
 assert f(C,R)['reason']=='DENY_EXTERNAL_REVIEW_SIGNATURE_INVALID'
 payload['candidate_sha256']='0'*64;review_file.write_text(json.dumps(payload,sort_keys=True))
 assert f(C,R)['reason']=='DENY_EXTERNAL_REVIEW_BINDING'
 public.chmod(0o666)
 assert f(C,R)['reason']=='DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED'
def test_missing_scientific_claims_fail_closed(review):
 f,p=review;dossier(p);out=f(C,R)
 assert out['decision']=='REJECT'
 assert out['reason']=='EXPLICIT_REQUIRED_SCIENTIFIC_EVIDENCE_MISSING'
 assert len(out['missing_prerequisites'])==4
 assert out['new_family_admitted'] is False
 assert out['research_execution_authorized'] is False

def test_non_boolean_verification_claim_fails_closed(review):
 f,p=review;x=dossier(p);assert_claims_for_review(p,x)
 name=x['novelty_file'];path=p/name;doc=json.loads(path.read_text())
 doc['mechanistic_novelty_independently_verified']='true'
 body=json.dumps(doc).encode();path.write_bytes(body)
 x['novelty_evidence_sha256']=hashlib.sha256(body).hexdigest();save(p,x)
 out=f(C,R)
 assert out['decision']=='REJECT'
 assert out['missing_prerequisites']==['novelty_file.mechanistic_novelty_independently_verified']
 assert out['research_execution_authorized'] is False

def test_explicit_scientific_failures_are_rejected_before_peer_review(review):
 f,p=review;x=dossier(p);assert_claims_for_review(p,x)
 cases=[('source_file','source_sha256','source_authenticity_independently_verified'),
        ('novelty_file','novelty_evidence_sha256','mechanistic_novelty_independently_verified'),
        ('replication_file','independent_replication_sha256','independent_experiment_replication_proven')]
 for name,key,flag in cases:
  path=p/x[name];doc=json.loads(path.read_text());doc[flag]=False
  raw=json.dumps(doc).encode();path.write_bytes(raw)
  x[key]=hashlib.sha256(raw).hexdigest()
 save(p,x);out=f(C,R)
 assert out['decision']=='REJECT'
 assert out['reason']=='EXPLICIT_REQUIRED_SCIENTIFIC_EVIDENCE_MISSING'
 assert len(out['missing_prerequisites'])==3
 assert out['new_family_admitted'] is False
 assert out['research_execution_authorized'] is False
 assert out['orders_allowed'] is False


def test_exhausted_self_attested_unknown_and_unsafe(review):
 f,p=review
 for change,reason in [({'native_family':'trend'},'DENY_EXISTING_OR_EXHAUSTED_FAMILY'),({'new_causal_evidence_verified':True},'DENY_SELF_ATTESTATION'),({'market':'UNKNOWN'},'DENY_UNKNOWN_MARKET'),({'orders_allowed':True},'DENY_UNSAFE')]:
  x=dossier(p);x.update(change);save(p,x);assert f(C,R)['reason']==reason
def test_tampered_hash_and_bound_identity(review):
 f,p=review;x=dossier(p);(p/x['novelty_file']).write_text('{}')
 assert f(C,R)['reason']=='EVIDENCE_HASH_MISMATCH'
 x=dossier(p);path=p/x['replication_file'];d=json.loads(path.read_text());d['market']='ETHUSD'
 raw=json.dumps(d).encode();path.write_bytes(raw);x['independent_replication_sha256']=hashlib.sha256(raw).hexdigest();save(p,x)
 assert f(C,R)['reason']=='EVIDENCE_IDENTITY_MISMATCH'
def test_path_links_and_size_bounds(review):
 f,p=review;x=dossier(p);x['source_file']='../outside.json';save(p,x)
 assert f(C,R)['reason']=='INVALID_EVIDENCE_PATH'
 x=dossier(p);path=p/x['source_file'];path.unlink();path.symlink_to('/nonexistent')
 assert f(C,R)['decision']=='REJECT'
 path.unlink();(p/'causal_family_candidate_v2.json').write_bytes(b' '*16385)
 assert f(C,R)['decision']=='REJECT'
def test_duplicate_hashes_and_bad_references(review):
 f,p=review;x=dossier(p);x['independent_replication_sha256']=x['source_sha256'];save(p,x)
 assert f(C,R)['reason']=='DENY_NONINDEPENDENT_HASHES'
 dossier(p);assert f({},R)['reason']=='INVALID_REFERENCE_INPUTS'
