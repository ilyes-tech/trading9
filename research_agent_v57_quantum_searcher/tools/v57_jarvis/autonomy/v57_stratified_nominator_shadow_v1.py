#!/usr/bin/env python3
import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3];SRC=ROOT/'work/autopilot_v433/cycles';OUT=ROOT/'work/v57_jarvis/V57_STRATIFIED_NOMINATOR_SHADOW_V1.json';CAP=4
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def sid(z):return (z.get('strategy') or {}).get('strategy_id') or z.get('strategy_id') or z.get('variant_id')
def desc(z):
 s=z.get('strategy') or {};m=s.get('market') or {};r=z.get('result') or {};c=z.get('candidate') or {};return {'market':m.get('symbol') or r.get('market') or c.get('market') or z.get('market'),'side':m.get('side') or r.get('side') or z.get('side'),'timeframe':m.get('timeframe') or r.get('timeframe') or c.get('timeframe') or z.get('timeframe')}
def qual(z):return z.get('quality') or z.get('result') or z
def exact(z):return qual(z).get('exact_pass') is True or z.get('exact_pass') is True
def score(z):
 q=qual(z);return (float(q.get('min_stress_pf',0)),float(q.get('min_base_pf',0)),float(q.get('worst_stress_avg_bps',0)),float(q.get('worst_base_avg_bps',0)),float(q.get('worst_drawdown_bps',-1e99)),sid(z) or '')
def main():
 uniq={}
 for p in sorted(SRC.rglob('*RECORDS*.jsonl')):
  for line in p.open(errors='ignore'):
   try:z=json.loads(line)
   except:continue
   i=sid(z)
   if i and exact(z):
    old=uniq.get(i)
    if old is None or score(z)>score(old):uniq[i]=z
 groups={}
 for z in uniq.values():
  x=desc(z);groups.setdefault((x['market'],x['side']),[]).append(z)
 selected=[];summary={}
 for k in sorted(groups,key=str):
  xs=sorted(groups[k],key=score,reverse=True);take=xs[:CAP];selected+=take;summary['|'.join(map(str,k))]={'eligible':len(xs),'selected':len(take),'best_min_stress_pf':score(xs[0])[0]}
 rows=[{'strategy_id':sid(z),'descriptor':desc(z),'objectives':qual(z)} for z in selected]
 out={'schema_version':1,'kind':'V57_STRATIFIED_NOMINATOR_SHADOW_V1','mode':'SHADOW_RESEARCH_ONLY','source':'work/autopilot_v433/cycles/*RECORDS*.jsonl','stratum':['market','side'],'cap_per_stratum':CAP,'eligible_exact_unique':len(uniq),'selected_count':len(rows),'summary':summary,'selected':rows,'safety':{'orders_allowed':False,'mt5_allowed':False,'holdout_read':False,'production_mutation':False}}
 out['selection_sha256']=hashlib.sha256(canon(rows).encode()).hexdigest();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
