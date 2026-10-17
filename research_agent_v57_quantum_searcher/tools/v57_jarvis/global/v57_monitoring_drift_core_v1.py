from dataclasses import dataclass
import math
@dataclass(frozen=True)
class Health:
 data_age_s:float; heartbeat_age_s:float; execution_divergences:int; drawdown:float; expected_trade_rate:float; observed_trade_rate:float
@dataclass(frozen=True)
class Thresholds:
 max_data_age_s:float=120.; max_heartbeat_age_s:float=60.; max_execution_divergences:int=0; max_drawdown:float=.10; max_trade_rate_ratio:float=2.; min_trade_rate_ratio:float=.5
def assess(h:Health,t:Thresholds=Thresholds()):
 reasons=[]
 vals=(h.data_age_s,h.heartbeat_age_s,h.execution_divergences,h.drawdown,h.expected_trade_rate,h.observed_trade_rate,t.max_data_age_s,t.max_heartbeat_age_s,t.max_execution_divergences,t.max_drawdown,t.max_trade_rate_ratio,t.min_trade_rate_ratio)
 if (any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or x<0 for x in vals)
     or not isinstance(h.execution_divergences,int) or not isinstance(t.max_execution_divergences,int)
     or t.max_trade_rate_ratio<1 or not 0<t.min_trade_rate_ratio<=1 or t.max_drawdown<=0):
  return {'state':'EMERGENCY','action':'STOP','reasons':['INVALID_INPUT'],'orders_allowed':False,'promotion_allowed':False}
 if h.data_age_s>t.max_data_age_s: reasons.append('STALE_DATA')
 if h.heartbeat_age_s>t.max_heartbeat_age_s: reasons.append('HEARTBEAT_LOST')
 if h.execution_divergences>t.max_execution_divergences: reasons.append('EXECUTION_DIVERGENCE')
 if h.drawdown>=t.max_drawdown: reasons.append('DRAWDOWN_LIMIT')
 if h.expected_trade_rate>0:
  r=h.observed_trade_rate/h.expected_trade_rate
  if r>t.max_trade_rate_ratio or r<t.min_trade_rate_ratio: reasons.append('TRADE_RATE_DRIFT')
 elif h.observed_trade_rate>0:
  reasons.append('TRADE_RATE_DRIFT')
 state='NORMAL' if not reasons else ('EMERGENCY' if any(x in reasons for x in ('INVALID_INPUT','HEARTBEAT_LOST','DRAWDOWN_LIMIT')) else 'DEGRADED')
 action={'NORMAL':'KEEP','DEGRADED':'QUARANTINE','EMERGENCY':'STOP'}[state]
 return {'state':state,'action':action,'reasons':reasons,'orders_allowed':False,'promotion_allowed':False}
