"""Synthetic native replay and evidence-file checks; no historical datasets."""
import copy
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
import hashlib,json,os
from pathlib import Path
import runpy,tempfile,unittest
from hf_lab.replay import ReplaySignal,ReplaySettings,Bar,_OpenTrade,_close_trade,_entry_execution_price
ROOT=Path('/home/trading/TradingAI-HF-Lab')
MODULE=Path(os.environ.get('OMEGA_COST_VERIFIER',str(ROOT/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_independent_evidence_verifier_v2.py')))
NS=runpy.run_path(str(MODULE));AUDIT=NS['audit_replay_costs'];FILE=NS['audit_trade_evidence_file']
SAFE=dict(orders_allowed=False,mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)

def native(side='BUY',risk=1,fee=5,slip=1):
    now=datetime(2026,1,1,tzinfo=timezone.utc);direction=1 if side=='BUY' else -1
    signal=ReplaySignal(strategy='SYNTHETIC',side=side,stop_distance=risk,target_distance=2*risk)
    settings=ReplaySettings(fee_bps_per_side=fee,slippage_bps_per_side=slip)
    entry=_entry_execution_price(side=side,raw_price=100,slippage_bps=slip)
    trade=_OpenTrade(trade_id=1,signal_id=1,symbol='TEST',signal=signal,signal_time=now-timedelta(minutes=1),entry_time=now,entry_index=1,raw_entry_price=100,entry_price=entry,stop_price=100-direction*risk,target_price=100+direction*2*risk,risk_distance=risk)
    bar=Bar(time=now+timedelta(minutes=1),open=101,high=102,low=99,close=101,trades=1)
    return asdict(_close_trade(trade=trade,bar=bar,raw_exit_price=101,result='SYNTHETIC',holding_bars=1,settings=settings))

class TradeCostEvidenceTests(unittest.TestCase):
    def test_native_long_short_and_risk_units(self):
        for side in ('BUY','SELL'):
            for risk in (1,2):
                result=AUDIT([native(side,risk)],5,1)
                self.assertEqual(result['status'],'COST_ARITHMETIC_VERIFIED_NOT_ADMITTED')
                self.assertIs(result['cost_realism_verified'],False)
                self.assertIs(result['new_research_authorized'],False)

    def test_tampered_metrics_or_execution_prices_rejected(self):
        for key in ('gross_r','net_r','fee_r','slippage_r','entry_price','exit_price'):
            trade=native();trade[key]+=0.01
            self.assertEqual(AUDIT([trade],5,1)['status'],'COST_REJECT')

    def test_invalid_costs_and_values_rejected(self):
        for x in (-1,float('nan'),float('inf'),True,'5'):
            self.assertEqual(AUDIT([native()],x,1)['status'],'COST_REJECT')
        trade=native();trade['net_r']=float('nan')
        self.assertEqual(AUDIT([trade],5,1)['status'],'COST_REJECT')
        self.assertEqual(AUDIT([],5,1)['status'],'COST_REJECT')
        self.assertEqual(AUDIT([native(fee=0,slip=0)],0,0)['status'],'COST_ARITHMETIC_VERIFIED_NOT_ADMITTED')

    def bundle(self,folder,trade=None):
        doc=dict(kind='V57_REPLAY_TRADE_COST_EVIDENCE_V1',strategy_sha256='a'*64,dataset_sha256='b'*64,settings=dict(fee_bps_per_side=5,slippage_bps_per_side=1),trades=[trade or native()],**SAFE)
        p=folder/'proof.json';p.write_text(json.dumps(doc,default=lambda x:x.isoformat()))
        return dict(evidence_file=p.name,evidence_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),strategy_sha256='a'*64,dataset_sha256='b'*64)

    def test_file_binding_and_no_independence_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);FILE.__globals__['S']=folder;candidate=self.bundle(folder)
            out=FILE(candidate)
            self.assertEqual(out['status'],'FILE_AND_COST_ARITHMETIC_VERIFIED_NOT_ADMITTED')
            for key in ('independent_replication_proven','new_research_authorized','dataset_contents_verified','preregistration_verified','causal_novelty_proven'):
                self.assertIs(out[key],False)
            self.assertEqual(FILE(dict(candidate,dataset_sha256='c'*64))['reason'],'MISMATCH_DATASET_SHA256')
            (folder/'proof.json').write_text('{}')
            self.assertEqual(FILE(candidate)['reason'],'DENY_HASH_OR_SIZE')

    def test_valid_hash_does_not_hide_incorrect_costs(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);FILE.__globals__['S']=folder;trade=native();trade['net_r']=999
            out=FILE(self.bundle(folder,trade))
            self.assertEqual(out['status'],'TRADE_EVIDENCE_REJECTED')
            self.assertEqual(out['reason'],'MISMATCH_NET_R')

    def test_missing_and_symlink_files_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);FILE.__globals__['S']=folder;candidate=self.bundle(folder)
            self.assertEqual(FILE(dict(candidate,evidence_file='../proof.json'))['reason'],'DENY_PATH')
            (folder/'link.json').symlink_to(folder/'proof.json')
            self.assertEqual(FILE(dict(candidate,evidence_file='link.json'))['reason'],'DENY_MISSING_OR_LINK')

if __name__=='__main__':unittest.main()
