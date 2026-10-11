import json,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');Q=R/'research_agent_v57_quantum_searcher';S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
for p in (Q/'tools/v57_jarvis/v3/registry',Q/'src',Q/'src/v433',Q/'src/v434',Q/'src/v435',Q/'src/v436',Q/'src/v437',Q/'src/v438'):sys.path.insert(0,str(p))
import v57_qd_orchestrator_engine_v438_v1 as O,v57_search_replay_v371_v1 as Replay,v57_auto_deep_validator_v3_8 as D
def main():
 d=json.loads((S/'agenda_probe_result_v1.json').read_text());hits=[x for x in d['result']['records'] if x.get('status')=='EVALUATED' and (x.get('result') or {}).get('exact_pass') is True]
 if len(hits)!=1:print('STOP|FAIL|AGENDA_DEEP|EXACT_PASS_COUNT='+str(len(hits)));return
 x=hits[0];st=x['strategy'];sid=st['strategy_id'];m=st['market'];ctx=O.base.adapter2.prepare_context(m['symbol'],m['timeframe']);rp=Replay.evaluate_strategy(ctx,st,O.signal6.bitcache.MaskBitsetCache())
 if rp.get('exact_pass') is not True:print('STOP|FAIL|AGENDA_DEEP|INDEPENDENT_REPLAY_NOT_EXACT');return
 deep=D.validate_dsl3(st,ctx,rp);out={'schema_version':1,'kind':'JARVIS_AGENDA_EXACTPASS_DEEP_V1','status':'COMPLETED','source_agenda_id':d['agenda_id'],'strategy_id':sid,'independent_replay_exact_pass':True,'deep':deep,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 t=S/'agenda_exactpass_deep_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'agenda_exactpass_deep_v1.json');print('ALL PASS|AGENDA_DEEP|'+deep['status']+'|'+sid[:12]+'|HOLDOUT=BLOCKED|ORDERS=BLOCKED')
if __name__=='__main__':main()
