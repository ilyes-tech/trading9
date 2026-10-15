#!/usr/bin/env python3
import hashlib,json,pathlib,sys
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 o=load('bounded_objective_v1.json');t=load('tool_selection_v1.json');r=load('resume_validation_v1.json')
 causal=load('causal_family_admission_v2.json');evidence=load('independent_evidence_verifier_v2.json')
 reasons=[]
 if causal.get('independent_evidence_verifier')!='TECHNICAL_VERIFIER_CONNECTED_NOT_SCIENTIFIC_ADMISSION':
  reasons.append('TECHNICAL_EVIDENCE_VERIFIER_NOT_VERIFIED')
 # The existing V2 verifier proves structural/numeric checks, not independent science.
 # Deliberately deny admission until a separately reviewed signed authorization
 # mechanism is implemented and tested; self-reported JSON flags never suffice.
 if causal.get('scientific_independent_admission')!='NOT_ESTABLISHED':
  reasons.append('UNTRUSTED_SCIENTIFIC_ADMISSION_STATUS')
 reasons.append('INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE')
 source=S/'multimarket_evidence_registry_v3.json';coverage=S/'native_capability_coverage_v2.json'
 try:
  if source.is_symlink() or evidence.get('source_sha256')!=hashlib.sha256(source.read_bytes()).hexdigest():reasons.append('EVIDENCE_PROVENANCE_INVALID')
  if coverage.is_symlink() or causal.get('coverage_sha256')!=hashlib.sha256(coverage.read_bytes()).hexdigest():reasons.append('CAUSAL_PROVENANCE_INVALID')
 except OSError:reasons.append('PROVENANCE_UNREADABLE')
 if causal.get('new_family_admitted') is not True or causal.get('research_execution_authorized') is not True:reasons.append('CAUSAL_ADMISSION_DENIED')
 if evidence.get('causal_novelty_proven') is not True or evidence.get('new_research_authorized') is not True:reasons.append('INDEPENDENT_EVIDENCE_MISSING')
 if o.get('status')!='OPEN_REVIEW_ONLY': reasons.append('NO_OPEN_BOUNDED_OBJECTIVE')
 if o.get('objective_type') not in {'HYPOTHESIS_REVIEW','FEEDBACK_REVIEW'}: reasons.append('OBJECTIVE_NOT_DISCOVERY_ELIGIBLE')
 if t.get('searcher_selected') is not True or 'SEARCHER' not in (t.get('selected') or []): reasons.append('SEARCHER_NOT_SELECTED')
 if r.get('decision') not in {'IDLE','SAFE_RESUME'}: reasons.append('RESUME_STATE_UNSAFE')
 # Phase-2 gate is authorization-only. It never launches the searcher itself.
 admitted=not reasons
 out={'schema_version':1,'kind':'JARVIS_SEARCH_AUTHORIZATION_GATE_V1','status':'AUTHORIZED' if admitted else 'DENIED','reasons':reasons,'authorized':admitted,'max_candidates':4 if admitted else 0,'next_required_capability':'VERIFY_INTEGRATED_TECHNICAL_EVIDENCE_PIPELINE' if 'TECHNICAL_EVIDENCE_VERIFIER_NOT_VERIFIED' in reasons else 'OBTAIN_EXTERNAL_SCIENTIFIC_REVIEW_AND_PROSPECTIVE_EVIDENCE','execution_started':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 review=evidence.get('replay_review')
 out['replay_review_status']=review.get('status') if isinstance(review,dict) else 'REVIEW_NOT_REPORTED'
 out['replay_review_reason']=review.get('reason') if isinstance(review,dict) else None
 p=S/'search_authorization_v1.json';q=S/'search_authorization_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(p)
 print(('ALL PASS' if admitted else 'DENIED')+'|SEARCH_AUTH_GATE_V1|AUTHORIZED='+str(admitted).upper()+'|REASONS='+(','.join(reasons) if reasons else 'NONE')+'|EXECUTION=NO');return 0 if admitted else 3
if __name__=='__main__':sys.exit(main())
