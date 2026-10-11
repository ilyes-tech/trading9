import hashlib,json,os,sqlite3,sys,time
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');os.chdir(R)
for p in [R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry',R/'research_agent_v57_quantum_searcher/src/v438',R/'research_agent_v57_quantum_searcher/src/v437',R/'research_agent_v57_quantum_searcher/src/v436',R/'research_agent_v57_quantum_searcher/src/v435',R/'research_agent_v57_quantum_searcher/src/v434',R/'research_agent_v57_quantum_searcher/src/v433',R/'research_agent_v57_quantum_searcher/src']:sys.path.insert(0,str(p))
DB=S/'agenda_probe_v1.sqlite3'
def main():
 h=json.loads((S/'agenda_hypothesis_v1.json').read_text())
 if h.get('experiment_class')!='BOUNDED_DEVELOPMENT_PROBE':print('ALL PASS|AGENDA_PROBE|SKIP');return
 hid=h['hypothesis_id']; cap=min(4,int(h.get('candidate_cap',4))); seed=800000+(int(hid[:8],16)%100000)
 c=sqlite3.connect(DB);c.execute('CREATE TABLE IF NOT EXISTS runs(hypothesis_id TEXT PRIMARY KEY,ts_ns INTEGER,status TEXT)');old=c.execute('SELECT status FROM runs WHERE hypothesis_id=?',(hid,)).fetchone()
 if old:print('ALL PASS|AGENDA_PROBE|IDEMPOTENT|'+old[0]);c.close();return
 mem=next(int(x.split()[1])//1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
 if mem<2048 or load>0.75:print('STOP|FAIL|AGENDA_PROBE|RESOURCE_GATE');c.close();return
 import v57_scientist_v3_4 as SCI
 statement=h['hypothesis']+'; space='+h['space']+'; distinct agenda='+h['agenda_id'];res=SCI.experiment(statement,start=0,count=cap,evaluate=True,seed=seed)
 out={'schema_version':1,'kind':'JARVIS_AGENDA_PROBE_RESULT_V1','status':'COMPLETED','agenda_id':h['agenda_id'],'hypothesis_id':hid,'hypothesis':statement,'seed':seed,'candidate_count':cap,'result':res,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 t=S/'agenda_probe_result_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'agenda_probe_result_v1.json');c.execute('INSERT INTO runs VALUES(?,?,?)',(hid,time.time_ns(),'COMPLETED'));c.commit();c.close();print('ALL PASS|AGENDA_PROBE|COMPLETED|CANDIDATES='+str(cap)+'|SEARCHER_DAEMON=NOT_USED')
if __name__=='__main__':main()
