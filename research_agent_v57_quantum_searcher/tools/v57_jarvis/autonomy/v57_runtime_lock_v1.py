#!/usr/bin/env python3
import fcntl,json,os,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');L=S/'jarvis_runtime_v1.lock';O=S/'runtime_lock_v1.json'
def write(status,reason=None):
 x={'schema_version':1,'kind':'JARVIS_RUNTIME_LOCK_V1','status':status,'pid':os.getpid(),'reason':reason,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()};t=O.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');t.replace(O)
def main():
 seconds=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
 L.parent.mkdir(parents=True,exist_ok=True);f=L.open('a+')
 try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:write('DENIED','LOCK_HELD');print('STOP|FAIL|RUNTIME_LOCK|LOCK_HELD');return 3
 write('ACQUIRED');print('ALL PASS|RUNTIME_LOCK|ACQUIRED|PID='+str(os.getpid()),flush=True)
 if seconds>0:time.sleep(seconds)
 fcntl.flock(f,fcntl.LOCK_UN);write('RELEASED');return 0
if __name__=='__main__':sys.exit(main())
