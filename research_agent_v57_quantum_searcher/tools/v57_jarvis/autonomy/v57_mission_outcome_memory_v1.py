import hashlib,json,time
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');SRC=S/'general_mission_last_v3.json';J=S/'mission_outcomes_v1.jsonl';ST=S/'mission_outcome_status_v1.json'
def main():
 if not SRC.exists(): print('STOP|FAIL|MISSION_OUTCOME_MEMORY|NO_MISSION');raise SystemExit(1)
 d=json.loads(SRC.read_text());steps=d.get('steps',[]);ok=d.get('status')=='COMPLETED' and all(x.get('status')=='PASS' for x in steps)
 rec={'ts_ns':time.time_ns(),'mission_id':d.get('mission_id'),'mission_kind':d.get('mission_kind'),'status':'SUCCESS' if ok else 'FAILURE','plan':d.get('plan',[]),'step_statuses':[x.get('status') for x in steps]}
 rec['fingerprint']=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 S.mkdir(parents=True,exist_ok=True)
 with J.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
 rows=[json.loads(x) for x in J.read_text().splitlines() if x.strip()];succ=sum(x['status']=='SUCCESS' for x in rows);fail=len(rows)-succ
 out={'schema_version':1,'kind':'JARVIS_MISSION_OUTCOME_MEMORY_V1','status':'PASS','entries':len(rows),'successes':succ,'failures':fail,'last_fingerprint':rec['fingerprint'],'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 t=ST.with_suffix('.tmp');t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(ST);print(f'ALL PASS|MISSION_OUTCOME_MEMORY|ENTRIES={len(rows)}|SUCCESS={succ}|FAILURE={fail}')
if __name__=='__main__':main()
