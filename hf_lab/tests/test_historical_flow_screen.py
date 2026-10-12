"""Synthetic history tests: no dataset, holdout, admission, or search execution."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path('/home/trading/TradingAI-HF-Lab')
MODULES = Path(os.environ.get('OMEGA_HISTORY_MODULES', str(ROOT / 'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')))
N = runpy.run_path(str(MODULES / 'v57_multimarket_novelty_review_v1.py'))
Q = runpy.run_path(str(MODULES / 'v57_multimarket_question_builder_v1.py'))
MARKETS = ['XAUUSD','BTCUSD','ETHUSD','LTCUSD','EURUSD','GBPUSD','USDJPY']
HEADER = 'stage,symbol,family,profile,horizon_seconds\n'
ROW = 'TRAIN,BTC/USD,FLOW_MOMENTUM,P01,60\n'

class HistoricalFlowScreenTests(unittest.TestCase):
    def parse(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.csv'
            path.write_text(content)
            return N['prior_search_summary'](path)

    def test_market_separation_and_horizon_counts(self):
        h = self.parse(HEADER + ROW + 'TRAIN,ETH/USD,FLOW_REVERSAL,P02,15\n')
        self.assertEqual(h['by_market']['BTCUSD']['sixty_second_horizon_count'], 1)
        self.assertEqual(h['by_market']['ETHUSD']['sixty_second_horizon_count'], 0)
        self.assertNotIn('LTCUSD', h['by_market'])
        self.assertEqual(len(h['source_sha256']), 64)

    def test_invalid_and_duplicate_records_are_not_clean_history(self):
        for data in [HEADER, HEADER + ROW + ROW, HEADER + ROW.replace('TRAIN','FINAL_TEST'), HEADER + ROW.replace('BTC/USD','LTC/USD'), HEADER + ROW.replace(',60',',nan'), HEADER + ROW.replace('FLOW_MOMENTUM','UNKNOWN')]:
            with self.subTest(data=data):
                h = self.parse(data)
                self.assertEqual(h['status'], 'UNAVAILABLE_OR_INVALID')
                self.assertEqual(h['by_market'], {})

    def test_missing_history_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            h = N['prior_search_summary'](Path(directory) / 'missing.csv')
        self.assertEqual(h['status'], 'UNAVAILABLE_OR_INVALID')

    def test_pipeline_preserves_denials_and_does_not_claim_ltc_novelty(self):
        history = self.parse(HEADER + ROW)
        queue = {'kind':'V57_MULTIMARKET_RESEARCH_QUEUE_V1','markets':[{'market':s} for s in MARKETS]}
        agenda = {'kind':'JARVIS_RESEARCH_AGENDA_V4','items':[]}
        review = N['review'](queue, agenda, history)
        features = {'kind':'V57_MULTIMARKET_FEATURE_ELIGIBILITY_V1','markets':[{'market':s,'bar_imbalance_feature_schema_supported':s in ('BTCUSD','LTCUSD')} for s in MARKETS]}
        questions = Q['build'](features, review)
        bymarket = {q['market']:q for q in questions['questions']}
        self.assertEqual(bymarket['BTCUSD']['historical_trial_count'],1)
        self.assertIsNone(bymarket['LTCUSD']['historical_trial_count'])
        self.assertEqual(bymarket['LTCUSD']['historical_trial_scope'],'NO_MATCH_IN_THIS_CAMPAIGN_NOT_PROOF_OF_NOVELTY')
        for doc in [review, questions]:
            for flag in ['novelty_proven','execution_authorized','orders_allowed','mt5_allowed','holdout_allowed']:
                self.assertIs(doc[flag],False)
        self.assertTrue(all(q['execution_authorized'] is False for q in questions['questions']))
        self.assertTrue(bymarket['BTCUSD']['history_overlap_not_ruled_out'])

if __name__ == '__main__':
    unittest.main()
