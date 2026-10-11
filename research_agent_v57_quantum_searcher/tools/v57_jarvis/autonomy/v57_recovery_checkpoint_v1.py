import hashlib,json,os,shutil,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");C=S/"checkpoints";C.mkdir(exist_ok=True)
FILES=["status_v5.json","research_feedback_v1.json","goal_queue_v2.json","tool_selection_v1.json","metacognition_v1.json","completion_audit_v5.json","integrity_status_v1.json"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stamp=str(time.time_ns());d=C/stamp;d.mkdir();manifest={}
 for n in FILES:
  p=S/n
  if p.exists():shutil.copy2(p,d/n);manifest[n]=sha(d/n)
 (d/"manifest.json").write_text(json.dumps({"schema_version":1,"created_ns":int(stamp),"files":manifest},indent=2,sort_keys=True)+"\n")
 # retain newest 5
 ds=sorted([x for x in C.iterdir() if x.is_dir()],key=lambda x:x.name)
 for x in ds[:-5]:shutil.rmtree(x)
 verify=all(sha(d/n)==h for n,h in manifest.items())
 out={"schema_version":1,"kind":"JARVIS_RECOVERY_CHECKPOINT_V1","status":"PASS" if verify else "FAIL","checkpoint":d.name,"files":len(manifest),"retained":min(len(ds),5),"restore_mode":"MANUAL_OR_FAIL_CLOSED_ONLY"}
 t=S/"checkpoint_status_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"checkpoint_status_v1.json")
 print(("ALL PASS" if verify else "STOP|FAIL")+"|RECOVERY_CHECKPOINT|FILES="+str(len(manifest))+"|RETAIN=5")
if __name__=="__main__":main()
