#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher')
sys.path[:0]=[str(R/'tools/v57_jarvis/v3/registry'),str(R/'src/v433')]
import v57_jarvis_integrated_v4 as I
import v57_materializer_v3_13 as M
import v57_post_materialization_replay_v3_14 as P14
STATE=R/'work/autopilot_v433/cumulative_state.json'
def gate(entry):
 s=entry['strategy']; ctx=I.O.base.adapter2.prepare_context(s['market']['symbol'],s['market']['timeframe'])
 m=M.materialize(s,ctx); r=P14.evaluate(s,ctx,m)
 passed=bool(entry.get('exact_pass')) and r['conclusion']=='POST_MATERIALIZATION_REPLAY_PASS'
 return {'strategy_id':s['strategy_id'],'search_exact_pass':bool(entry.get('exact_pass')),'fixed_exact_pass':bool(r['fixed_replay']['exact_pass']),'fixed_min_stress_pf':r['fixed_replay'].get('min_stress_pf'),'conclusion':'DEPLOYMENT_VERIFIED' if passed else 'DEPLOYMENT_REJECTED','promotion_allowed':passed,'research_integrity':r['research_integrity']}
def main():
 x=json.loads(STATE.read_text()); b=x['archive']['exact_backlog']; ids=list(b)[:int(sys.argv[1]) if len(sys.argv)>1 else 3]
 out=[gate(b[i]) for i in ids]; print(json.dumps(out,sort_keys=True));
 if any(z['research_integrity'].get('holdout_read') or z['research_integrity'].get('orders_allowed') for z in out): raise SystemExit(2)
if __name__=='__main__': main()
