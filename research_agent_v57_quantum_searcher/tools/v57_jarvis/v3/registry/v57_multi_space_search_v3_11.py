import v57_science_loop_v3_9 as L
ENGINE="V57_JARVIS_MULTI_SPACE_SEARCH_V3_11"
SPACES=[
("XAUUSD","M5","LONG","momentum trend"),
("XAUUSD","M5","SHORT","momentum trend"),
("XAUUSD","M15","LONG","momentum trend"),
("XAUUSD","M30","LONG","momentum trend"),
("XAUUSD","M30","SHORT","momentum trend"),
("XAUUSD","H1","LONG","momentum trend"),
("XAUUSD","H1","SHORT","momentum trend"),
("EURUSD","M15","LONG","momentum trend"),
("EURUSD","M15","SHORT","momentum trend"),
("GBPUSD","M15","LONG","momentum trend"),
("GBPUSD","M15","SHORT","momentum trend"),
("USDJPY","M15","LONG","momentum trend"),
("USDJPY","M15","SHORT","momentum trend"),
("BTCUSD","M15","LONG","momentum trend"),
("BTCUSD","M15","SHORT","momentum trend"),
("ETHUSD","M15","LONG","momentum trend"),
("ETHUSD","M15","SHORT","momentum trend"),
]
def run(seed_start=700000,batches_per_space=16):
 rows=[]
 for si,(market,tf,side,families) in enumerate(SPACES):
  seed=int(seed_start)+si*1000
  h="cherche et teste une stratégie "+market+" "+tf+" "+side+" "+families
  x=L.run(h,seed,int(batches_per_space))
  exact=sum(b["exact_pass"] for b in x["batches"])
  deep=sum(d["status"]=="DEEP_PASS" for b in x["batches"] for d in b["deep"])
  row={"market":market,"timeframe":tf,"side":side,"families":families,"seed_start":seed,"batches":len(x["batches"]),"exact_pass":exact,"deep_pass":deep,"status":x["status"]}
  rows.append(row)
  if x["status"]=="DEEP_PASS_FOUND":
   return {"engine":ENGINE,"status":"DEEP_PASS_FOUND","space":row,"strategy":x["strategy"],"winner":x["winner"],"seed":x["seed"],"candidate_index":x["candidate_index"],"spaces":rows,"orders_allowed":False,"holdout_allowed":False}
 return {"engine":ENGINE,"status":"SEARCH_BUDGET_EXHAUSTED","spaces":rows,"orders_allowed":False,"holdout_allowed":False}
