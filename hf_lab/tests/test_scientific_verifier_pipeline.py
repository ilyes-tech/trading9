"""Stage03 technical-verifier integration must not be mistaken for admission."""
import hashlib
import json
import runpy
from pathlib import Path

A = Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
SAFE = dict(orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
            auto_promotion_allowed=False)


def write(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True))


def test_technical_verifier_integrated_but_no_scientific_admission(tmp_path):
    ns = runpy.run_path(str(A / 'v57_causal_family_admission_v2.py'))
    verify = ns['technical_verifier_status']
    verify.__globals__['S'] = tmp_path
    assert verify() == 'TECHNICAL_VERIFIER_NOT_VERIFIED'
    registry = tmp_path / 'multimarket_evidence_registry_v3.json'
    registry.write_text('{"synthetic_registry": true}')
    evidence = dict(kind='V57_INDEPENDENT_EVIDENCE_VERIFIER_V2', status='PASS',
                    source_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
                    source_schema_checked=True,
                    trade_robustness_evaluation_supported=True,
                    trade_cost_arithmetic_supported=True,
                    temporal_metadata_checks_supported=True,
                    composed_replay_review_supported=True,
                    new_research_authorized=False, causal_novelty_proven=False, **SAFE,
                    stage03_initial_readiness=dict(
                        kind='OMEGA_STAGE03_PREEXPERIMENT_READINESS_V1',
                        development_experiment_authorized=False,
                        new_research_authorized=False, causal_novelty_proven=False, **SAFE))
    artifact = tmp_path / 'independent_evidence_verifier_v2.json'
    write(artifact, evidence)
    assert verify() == 'TECHNICAL_VERIFIER_CONNECTED_NOT_SCIENTIFIC_ADMISSION'
    evidence['causal_novelty_proven'] = True
    write(artifact, evidence)
    assert verify() == 'TECHNICAL_VERIFIER_NOT_VERIFIED'
    evidence['causal_novelty_proven'] = False
    evidence['source_sha256'] = 'f' * 64
    write(artifact, evidence)
    assert verify() == 'TECHNICAL_VERIFIER_NOT_VERIFIED'
    evidence['source_sha256'] = hashlib.sha256(registry.read_bytes()).hexdigest()
    write(artifact, evidence)
    artifact.unlink()
    artifact.symlink_to(registry)
    assert verify() == 'TECHNICAL_VERIFIER_NOT_VERIFIED'


def test_search_gate_never_trusts_forged_admission_flags(tmp_path):
    ns = runpy.run_path(str(A / 'v57_search_authorization_gate_v1.py'))
    main = ns['main']
    main.__globals__['S'] = tmp_path
    registry = tmp_path / 'multimarket_evidence_registry_v3.json'
    registry.write_text('{"synthetic": true}')
    coverage = tmp_path / 'native_capability_coverage_v2.json'
    coverage.write_text('{"synthetic": true}')
    write(tmp_path / 'causal_family_admission_v2.json',
          dict(new_family_admitted=True, research_execution_authorized=True,
               independent_evidence_verifier='TECHNICAL_VERIFIER_CONNECTED_NOT_SCIENTIFIC_ADMISSION',
               scientific_independent_admission='NOT_ESTABLISHED',
               coverage_sha256=hashlib.sha256(coverage.read_bytes()).hexdigest()))
    write(tmp_path / 'independent_evidence_verifier_v2.json',
          dict(source_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
               causal_novelty_proven=True, new_research_authorized=True))
    write(tmp_path / 'bounded_objective_v1.json',
          dict(status='OPEN_REVIEW_ONLY', objective_type='HYPOTHESIS_REVIEW'))
    write(tmp_path / 'tool_selection_v1.json',
          dict(searcher_selected=True, selected=['SEARCHER']))
    write(tmp_path / 'resume_validation_v1.json', dict(decision='IDLE'))
    assert main() == 3
    decision = json.loads((tmp_path / 'search_authorization_v1.json').read_text())
    assert decision['authorized'] is False
    assert decision['max_candidates'] == 0
    assert decision['orders_allowed'] is False
    assert 'INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE' in decision['reasons']
    assert decision['next_required_capability'] == 'OBTAIN_EXTERNAL_SCIENTIFIC_REVIEW_AND_PROSPECTIVE_EVIDENCE'
    forged = json.loads((tmp_path / 'causal_family_admission_v2.json').read_text())
    forged['scientific_independent_admission'] = 'VERIFIED_EXTERNAL_ADMISSION'
    write(tmp_path / 'causal_family_admission_v2.json', forged)
    assert main() == 3
    decision = json.loads((tmp_path / 'search_authorization_v1.json').read_text())
    assert 'UNTRUSTED_SCIENTIFIC_ADMISSION_STATUS' in decision['reasons']
    assert decision['authorized'] is False



def test_scientific_search_gate_future_max_budget_is_one_without_permission():
    """The eventual global admission must not offer 4 candidates for a one-shot protocol."""
    ns = runpy.run_path(str(A / 'v57_search_authorization_gate_v1.py'))
    source = (A / 'v57_search_authorization_gate_v1.py').read_text()
    assert "'max_candidates':1 if admitted else 0" in source
    assert "reasons.append('INDEPENDENT_SCIENTIFIC_ADMISSION_NOT_AVAILABLE')" in source
    assert callable(ns['main'])


def test_secondary_search_execution_gate_rejects_forged_authorization_without_independent_proof(tmp_path):
    """A forged authorization document cannot start or make the Searcher READY."""
    ns = runpy.run_path(str(A / 'v57_search_execution_gate_v1.py'))
    main = ns['main']
    main.__globals__['S'] = tmp_path
    write(tmp_path / 'bounded_objective_v1.json', {'objective_id': 'SYNTHETIC_UNAPPROVED'})
    for candidate_budget in (1, 2, 4):
        write(tmp_path / 'search_authorization_v1.json', {
            'status': 'AUTHORIZED', 'authorized': True, 'reasons': [],
            'max_candidates': candidate_budget, 'execution_started': False,
            'orders_allowed': False, 'mt5_allowed': False, 'holdout_allowed': False,
        })
        assert main() == 3
        actual = json.loads((tmp_path / 'search_execution_gate_v1.json').read_text())
        assert actual['status'] == 'DENIED'
        assert actual['ready'] is False
        assert actual['search_process_started'] is False
        assert actual['budget_candidates'] == 0
        assert actual['execution_token'] is None
        assert actual['orders_allowed'] is False
        assert 'INDEPENDENT_SCIENTIFIC_EXECUTION_AUTHORITY_NOT_PROVISIONED' in actual['reasons']
        if candidate_budget != 1:
            assert 'ONE_CANDIDATE_EXPERIMENT_BUDGET_REQUIRED' in actual['reasons']


def test_secondary_search_execution_gate_rejects_malformed_authorization(tmp_path):
    ns = runpy.run_path(str(A / 'v57_search_execution_gate_v1.py'))
    main = ns['main']
    main.__globals__['S'] = tmp_path
    write(tmp_path / 'bounded_objective_v1.json', {'objective_id':'TEST_NO_EXECUTION'})
    for status, reasons, budget in (('DENIED', [], 1), ('AUTHORIZED', ['REVIEW_MISSING'], 1),
                                     ('AUTHORIZED', [], True), ('AUTHORIZED', [], 0)):
        write(tmp_path / 'search_authorization_v1.json', {
            'status':status, 'authorized': True,'reasons':reasons,
            'max_candidates':budget,'execution_started':False,
        })
        assert main() == 3
        gate=json.loads((tmp_path/'search_execution_gate_v1.json').read_text())
        assert gate['status']=='DENIED' and gate['ready'] is False
        assert gate['search_process_started'] is False and gate['execution_token'] is None
