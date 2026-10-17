"""Stage08E: verify the legacy advisory tool selector without ever starting Searcher.

All inputs and outputs are isolated synthetic JSON fixtures in tmp_path.
Selection != scientific admission; execution guard remains separate and DENIED.
"""
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / 'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_tool_selector_v1.py'


def write(path, name, payload):
    (path / name).write_text(json.dumps(payload,sort_keys=True))


def choose(tmp_path, *, reflection=None, diagnosis=None, objective=None, causal=None, evidence=None):
    write(tmp_path, 'reflection_v2.json', reflection or {'next_action':'NONE'})
    write(tmp_path, 'failure_diagnosis_v2.json', diagnosis or {'status':'UNKNOWN'})
    if objective is not None:
        write(tmp_path, 'bounded_objective_v1.json', objective)
    if causal is not None:
        write(tmp_path, 'causal_family_admission_v2.json', causal)
    if evidence is not None:
        write(tmp_path, 'independent_evidence_verifier_v2.json', evidence)
    main=runpy.run_path(str(MODULE))['main']
    main.__globals__['S']=tmp_path
    main()
    x=json.loads((tmp_path / 'tool_selection_v1.json').read_text())
    assert x['status']=='PASS'
    assert x['orders_allowed'] is False
    assert x['mt5_allowed'] is False
    assert x['holdout_allowed'] is False
    assert x['searcher_selected']==('SEARCHER' in x['selected'])
    assert 'execution_authorized' not in x or x['execution_authorized'] is False
    return x


def test_missing_evidence_chooses_only_two_cheap_review_tools(tmp_path):
    r=choose(tmp_path)
    assert r['selected']==['MEMORY','REFLECTION']
    assert sum(r['catalog'][name]['cost'] for name in r['selected'])==2
    assert r['searcher_selected'] is False


def test_diagnosed_failure_uses_causal_tools_without_search(tmp_path):
    r=choose(tmp_path,diagnosis={'status':'DIAGNOSED'})
    assert r['selected']==['DIAGNOSIS','CAUSAL_DESIGN']
    assert r['reason']=='KNOWN_FAILURE_USE_CHEAP_CAUSAL_TOOLS_FIRST'
    assert sum(r['catalog'][name]['cost'] for name in r['selected'])==2
    assert r['searcher_selected'] is False


def test_prior_deep_evidence_chooses_replay_and_validator_but_does_not_execute(tmp_path):
    r=choose(tmp_path,reflection={'next_action':'ANALYZE_EXISTING_DEEP_EVIDENCE'})
    assert r['selected']==['REPLAY','DEEP_VALIDATOR']
    assert sum(r['catalog'][name]['cost'] for name in r['selected'])==5
    assert r['searcher_selected'] is False


@pytest.mark.parametrize('omission', ['objective','causal','evidence'])
def test_partial_claims_do_not_select_searcher(tmp_path, omission):
    docs={
        'objective':{'status':'OPEN_REVIEW_ONLY','objective_type':'HYPOTHESIS_REVIEW'},
        'causal':{'new_family_admitted':True,'research_execution_authorized':True},
        'evidence':{'causal_novelty_proven':True,'new_research_authorized':True},
    }
    docs.pop(omission)
    r=choose(tmp_path,**docs)
    assert r['selected']==['MEMORY','REFLECTION']
    assert r['searcher_selected'] is False


def test_self_reported_synthetic_approval_is_only_advisory_never_executed(tmp_path):
    # Fake JSON here is NOT a permission mechanism, test only the tool chooser.
    r=choose(tmp_path,
        objective={'status':'OPEN_REVIEW_ONLY','objective_type':'HYPOTHESIS_REVIEW'},
        causal={'new_family_admitted':True,'research_execution_authorized':True},
        evidence={'causal_novelty_proven':True,'new_research_authorized':True},
    )
    assert r['selected']==['SEARCHER']
    assert r['reason']=='CAUSAL_DISCOVERY_ADMITTED_REQUIRES_EXECUTION_GATE'
    assert r['searcher_selected'] is True
    assert not (tmp_path / 'search_authorization_v1.json').exists()
    assert not (tmp_path / 'search_execution_gate_v1.json').exists()


def test_repeat_synthetic_selection_is_deterministic(tmp_path):
    a=choose(tmp_path,diagnosis={'status':'DIAGNOSED'})
    b=choose(tmp_path,diagnosis={'status':'DIAGNOSED'})
    assert a==b
