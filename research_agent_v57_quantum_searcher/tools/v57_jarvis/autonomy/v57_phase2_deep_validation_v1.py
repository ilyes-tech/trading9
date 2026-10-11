#!/usr/bin/env python3
import json,pathlib,sys,time
ROOT=pathlib.Path('/home/trading/TradingAI-HF-Lab');Q=ROOT/'research_agent_v57_quantum_searcher';S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
for p in (Q/'tools/v57_jarvis/v3/registry',Q/'src',Q/'src/v433',Q/'src/v434',Q/'src/v435',Q/'src/v436',Q/'src/v437',Q/'src/v438'):sys.path.insert(0,str(p))
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 tri=load('phase2_result_triage_v1.json');src=load('phase2_scientific_result_v1.json');tok=tri.get('execution_token');reasons=[]
 if tri.get('decision')!='VALIDATION_REQUIRED' or tri.get('deep_validation_allowed') is not True:reasons.append('TRIAGE_NOT_VALIDATION_REQUIRED')
 if not tok or src.get('execution_token')!=tok:reasons.append('TOKEN_BINDING_INVALID')
 recs=(src.get('result') or {}).get('records') or [];hits=[x for x in recs if x.get('status')=='EVALUATED' and (x.get('result') or {}).get('exact_pass') is True]
 if len(hits)!=1:reasons.append('EXACT_PASS_COUNT_'+str(len(hits)))
 if reasons:print('STOP|FAIL|PHASE2_DEEP|'+','.join(reasons));return 3
 import v57_qd_orchestrator_engine_v438_v1 as O,v57_search_replay_v371_v1 as Replay,v57_auto_deep_validator_v3_8 as D
 x=hits[0];st=x['strategy'];sid=st['strategy_id'];m=st['market'];ctx=O.base.adapter2.prepare_context(m['symbol'],m['timeframe']);rp=Replay.evaluate_strategy(ctx,st,O.signal6.bitcache.MaskBitsetCache())
 if rp.get('exact_pass') is not True:print('STOP|FAIL|PHASE2_DEEP|INDEPENDENT_REPLAY_NOT_EXACT');return 3
 deep=D.validate_dsl3(st,ctx,rp);out={'schema_version':1,'kind':'JARVIS_PHASE2_DEEP_VALIDATION_V1','status':'COMPLETED','execution_token':tok,'strategy_id':sid,'independent_replay_exact_pass':True,'deep':deep,'pool_mutation_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()};q=S/'phase2_deep_validation_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_deep_validation_v1.json');print('ALL PASS|PHASE2_DEEP|'+deep['status']+'|'+sid[:12]+'|POOL_MUTATION=NO');return 0
if __name__=='__main__':sys.exit(main())
