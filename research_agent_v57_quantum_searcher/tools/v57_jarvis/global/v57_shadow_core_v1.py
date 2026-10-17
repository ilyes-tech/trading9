from dataclasses import dataclass,asdict
import math
from hashlib import sha256
import json
@dataclass(frozen=True)
class ShadowEvent:
 strategy_id:str; symbol:str; side:str; volume:float; expected_entry:float; observed_price:float; spread:float; latency_ms:float; ts:str
def evaluate(e, max_spread, max_latency_ms, max_price_gap):
 vals=(e.volume,e.expected_entry,e.observed_price,e.spread,e.latency_ms,max_spread,max_latency_ms,max_price_gap)
 if any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or x<0 for x in vals) or min(e.volume,e.expected_entry,e.observed_price)<=0:
  return {'status':'REJECT','reason':'INVALID_INPUT','orders_allowed':False,'promotion_allowed':False}
 gap=abs(e.observed_price-e.expected_entry)
 reasons=[]
 if e.spread>max_spread: reasons.append('SPREAD')
 if e.latency_ms>max_latency_ms: reasons.append('LATENCY')
 if gap>max_price_gap: reasons.append('PRICE_GAP')
 payload=json.dumps(asdict(e),sort_keys=True,separators=(',',':'))
 return {'status':'SHADOW_OK' if not reasons else 'SHADOW_DEGRADED','reasons':reasons,'price_gap':gap,'event_id':sha256(payload.encode()).hexdigest(),'orders_allowed':False,'promotion_allowed':False}
