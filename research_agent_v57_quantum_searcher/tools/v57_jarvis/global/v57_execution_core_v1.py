from dataclasses import dataclass
from hashlib import sha256
import json,math
@dataclass(frozen=True)
class Intent:
 strategy_id:str; symbol:str; side:str; volume:float; sl:float; tp:float; nonce:str

def canonical(i): return json.dumps(i.__dict__,sort_keys=True,separators=(',',':'),allow_nan=False)
def intent_id(i): return sha256(canonical(i).encode()).hexdigest()
def _positive_finite(value):
 return type(value) in (int,float) and math.isfinite(value) and value>0
def validate(i, risk_decision, market_fresh=True, broker_healthy=True, mode='SHADOW'):
 if mode not in {'SHADOW','DEMO_DISABLED','LIVE_DISABLED'}: return {'status':'DENY','reason':'INVALID_MODE','send_allowed':False}
 if risk_decision not in {'AUTHORIZE','REDUCE'}: return {'status':'DENY','reason':'RISK_DENIED','send_allowed':False}
 if market_fresh is not True: return {'status':'DENY','reason':'STALE_MARKET','send_allowed':False}
 if broker_healthy is not True: return {'status':'DENY','reason':'BROKER_UNHEALTHY','send_allowed':False}
 if i.side not in {'BUY','SELL'} or any(not _positive_finite(value) for value in (i.volume,i.sl,i.tp)): return {'status':'DENY','reason':'INVALID_INTENT','send_allowed':False}
 return {'status':'ACCEPT_SHADOW','reason':'VALIDATED','send_allowed':False,'intent_id':intent_id(i)}
class Deduplicator:
 def __init__(self): self.seen=set()
 def accept(self,i):
  x=intent_id(i)
  if x in self.seen:return False
  self.seen.add(x);return True

def reconcile(expected, observed, price_tol=1e-9, volume_tol=1e-12):
    if not isinstance(expected,dict) or not isinstance(observed,dict):
        return {'status':'DIVERGENCE','mismatches':['INVALID_EVENT'],'promotion_allowed':False,'send_allowed':False}
    keys=('symbol','side')
    mismatches=[k for k in keys if expected.get(k)!=observed.get(k)]
    for k,t in [('volume',volume_tol),('entry',price_tol),('sl',price_tol),('tp',price_tol)]:
        try:
            a,b=expected.get(k),observed.get(k)
            x,y=float(a),float(b)
            if (isinstance(a,bool) or isinstance(b,bool) or
                not _positive_finite(x) or not _positive_finite(y) or
                type(t) not in (int,float) or not math.isfinite(t) or t<0 or
                not math.isfinite(x-y) or abs(x-y)>t):
                mismatches.append(k)
        except (TypeError,ValueError,OverflowError):mismatches.append(k)
    return {'status':'PARITY' if not mismatches else 'DIVERGENCE','mismatches':mismatches,'promotion_allowed':False,'send_allowed':False}

def digital_twin(expected_events, observed_events):
    if len(expected_events)!=len(observed_events): return {'status':'DIVERGENCE','reason':'EVENT_COUNT','first_divergence':min(len(expected_events),len(observed_events)),'promotion_allowed':False}
    for n,(e,o) in enumerate(zip(expected_events,observed_events)):
        r=reconcile(e,o)
        if r['status']!='PARITY': return {'status':'DIVERGENCE','reason':'EVENT_MISMATCH','first_divergence':n,'detail':r,'promotion_allowed':False}
    return {'status':'PARITY','events':len(expected_events),'promotion_allowed':False}
