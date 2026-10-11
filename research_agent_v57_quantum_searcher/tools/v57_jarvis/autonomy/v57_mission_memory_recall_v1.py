import json
from collections import Counter
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');J=S/'mission_outcomes_v1.jsonl';O=S/'mission_memory_recall_v1.json'
def recall(kind=None):
 rows=[json.loads(x) for x in J.read_text().splitlines() if x.strip()] if J.exists() else []
 xs=[x for x in rows if not kind or x.get('mission_kind')==kind];c=Counter(x.get('status') for x in xs);last=xs[-1] if xs else None
 return {'schema_version':1,'kind':'JARVIS_MISSION_MEMORY_RECALL_V1','status':'PASS','query_kind':kind,'matches':len(xs),'successes':c['SUCCESS'],'failures':c['FAILURE'],'last':last,'advice':'REUSE_PROVEN_PLAN' if xs and c['FAILURE']==0 else ('REVIEW_FAILURES' if c['FAILURE'] else 'NO_PRIOR_EXPERIENCE'),'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
def main():
 import sys;o=recall(sys.argv[1] if len(sys.argv)>1 else None);t=O.with_suffix('.tmp');t.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');t.replace(O);print(f"ALL PASS|MISSION_MEMORY_RECALL|MATCHES={o['matches']}|SUCCESS={o['successes']}|FAILURE={o['failures']}|ADVICE={o['advice']}")
if __name__=='__main__':main()
