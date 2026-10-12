"""Synthetic robustness and parity tests; never replay historical data."""
import ast
import copy
import os
from pathlib import Path
import runpy
import unittest
import numpy as np

ROOT = Path('/home/trading/TradingAI-HF-Lab')
MODULE = Path(os.environ.get('OMEGA_NUMERIC_VERIFIER', str(ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_independent_evidence_verifier_v2.py')))
ASSESS = runpy.run_path(str(MODULE))['assess_trade_robustness']
SID = '1234567890abcdef'*4

def fixture():
    return [[dict(entry_time=(1000+fold*30+day)*86400+i*120,exit_time=(1000+fold*30+day)*86400+i*120+60,stress_net_bps=value)
             for day in range(20) for i,value in enumerate((-1,2,2))] for fold in range(3)]

class IndependentTradeRobustnessTests(unittest.TestCase):
    def test_positive_numeric_result_never_grants_admission(self):
        rows=fixture(); saved=copy.deepcopy(rows);out=ASSESS(rows,SID)
        self.assertEqual(out['status'],'ROBUSTNESS_PASS_NOT_ADMITTED')
        self.assertEqual(rows,saved)
        self.assertEqual(out,ASSESS(rows,SID))
        for key in ('causal_novelty_proven','independent_replication_proven','new_research_authorized','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed'):
            self.assertIs(out[key],False)

    def test_negative_returns_rejected(self):
        rows=fixture()
        for fold in rows:
            for trade in fold:trade['stress_net_bps']=-abs(trade['stress_net_bps'])
        out=ASSESS(rows,SID)
        self.assertEqual(out['status'],'ROBUSTNESS_REJECT')
        self.assertFalse(out['checks']['bootstrap_mean'])
        self.assertFalse(out['checks']['bootstrap_pf'])

    def test_concentrated_profit_rejected(self):
        rows=fixture();rows[0][1]['stress_net_bps']=10000
        out=ASSESS(rows,SID)
        self.assertEqual(out['status'],'ROBUSTNESS_REJECT')
        self.assertFalse(out['checks']['trade_concentration'])
        self.assertFalse(out['checks']['day_concentration'])

    def test_invalid_values_and_overlap_fail_closed(self):
        for value in (float('nan'),float('inf'),True,'2',10**400):
            rows=fixture();rows[0][0]['stress_net_bps']=value
            self.assertEqual(ASSESS(rows,SID)['status'],'ROBUSTNESS_INPUT_REJECTED')
        rows=fixture();rows[1][0]['entry_time']=rows[0][-1]['entry_time']
        self.assertEqual(ASSESS(rows,SID)['reason'],'NONCHRONOLOGICAL_OR_OVERLAPPING_TRADES')
        rows=fixture();rows[0][0]['exit_time']=rows[0][0]['entry_time']
        self.assertEqual(ASSESS(rows,SID)['reason'],'INVALID_TIMESTAMPS')

    def test_empty_hash_and_resource_limits(self):
        self.assertEqual(ASSESS([[],[],[]],SID)['status'],'ROBUSTNESS_INPUT_REJECTED')
        self.assertEqual(ASSESS(fixture(),'bad')['reason'],'INVALID_STRATEGY_HASH')
        self.assertEqual(ASSESS([[{}]*100001,[{}],[{}]],SID)['reason'],'TRADE_BUDGET_EXCEEDED')

    def test_insufficient_days_cannot_pass_bootstrap(self):
        rows=[[dict(entry_time=(1000+f)*86400+i*120,exit_time=(1000+f)*86400+i*120+60,stress_net_bps=1) for i in range(30)] for f in range(3)]
        out=ASSESS(rows,SID)
        self.assertEqual(out['status'],'ROBUSTNESS_REJECT')
        self.assertEqual(out['folds'][0]['p_mean_gt0'],0)

    def test_parity_with_existing_deep_math_without_importing_engine(self):
        source=ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry/v57_auto_deep_validator_v3_8.py'
        names={'pf','bootstrap_days','concentration','half_stats'}
        selected=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
        self.assertEqual(len(selected),4)
        reference={'np':np,'BOOT_N':1000}
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),reference)
        rows=fixture()
        for fold in rows:
            for i,trade in enumerate(fold):trade['stress_net_bps']=(i%7)-3
        out=ASSESS(rows,SID);seed=int(SID[:16],16)%(2**32)
        for index,fold in enumerate(rows):
            original=[{'entry_time':q['entry_time'],'stress':q['stress_net_bps']} for q in fold]
            boot=reference['bootstrap_days'](original,seed+index)
            concentration=reference['concentration'](original)
            halves=reference['half_stats'](original)
            result=out['folds'][index]
            self.assertEqual(result['p_mean_gt0'],boot['p_mean_gt0'])
            self.assertEqual(result['p_pf_ge1'],boot['p_pf_ge1'])
            self.assertAlmostEqual(result['max_trade_profit_share'],concentration['max_trade_profit_share'])
            self.assertAlmostEqual(result['max_day_profit_share'],concentration['max_day_profit_share'])
            self.assertEqual(result['positive_halves'],sum(h['trades']>=10 and h['stress_avg_bps']>0 for h in halves))

if __name__=='__main__':unittest.main()
