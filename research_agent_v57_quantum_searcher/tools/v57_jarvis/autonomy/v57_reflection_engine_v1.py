import json,sqlite3
from collections import Counter,defaultdict
from pathlib import Path
DB=Path("/home/trading/.local/state/tradingai/jarvis-v438/learning_memory_v1.sqlite3")
OUT=Path("/home/trading/.local/state/tradingai/jarvis-v438/reflection_v1.json")
def main():
 c=sqlite3.connect(DB); rows=c.execute("SELECT space,status,decision,reason,strategy_id,evidence_path FROM observations").fetchall(); c.close()
 if not rows: raise RuntimeError("NO_MEMORY")
 by=defaultdict(Counter)
 for space,status,decision,reason,sid,path in rows:
  market,tf,side=space.split("_",2); by["market"][market]+=1; by["timeframe"][tf]+=1; by["side"][side]+=1
 decisions=Counter(r[2] for r in rows)
 deep=[r for r in rows if r[2]=="REJECTED_DEEP"]
 focus=[]
 for r in deep:
  focus.append({"space":r[0],"reason":r[3],"strategy_id":r[4],"priority":"ANALYZE_DEEP_REJECTION"})
 if not focus:
  for r in rows[:8]: focus.append({"space":r[0],"reason":r[3],"strategy_id":r[4],"priority":"DIVERSIFY_HYPOTHESIS"})
 x={"schema_version":1,"kind":"JARVIS_REFLECTION_V1","status":"READY","observations":len(rows),"decision_counts":dict(decisions),"interpretation":{"dominant_failure":"NO_EXACT_PASS" if decisions.get("NO_EXACT_PASS",0)>len(rows)/2 else "MIXED","deep_rejections":len(deep),"rule":"DO_NOT_REPEAT_IDENTICAL_GLOBAL_SEARCH; analyze strongest failure evidence before allocating new compute"},"focus":focus,"next_action":"CRITIQUE_DEEP_REJECTION" if deep else "DIVERSIFY_HYPOTHESIS","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 OUT.parent.mkdir(parents=True,exist_ok=True); t=OUT.with_suffix(".tmp"); t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n"); t.replace(OUT)
 print("ALL PASS|REFLECTION_V1|OBS="+str(len(rows))+"|NEXT="+x["next_action"])
if __name__=="__main__": main()
