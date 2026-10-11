import hashlib,time
PLANS={'SAFETY':['SAFETY'],'STATUS':['HEALTH'],'AGENDA':['AGENDA','HEALTH'],'CONTINUE':['STRATEGY_POOL','AGENDA','GOALS','TOOLS','HEALTH'],'GOALS':['GOALS','HEALTH'],'REFLECTION':['REFLECTION','HEALTH'],'CAPABILITY_GAPS':['CAPABILITY_GAPS','HEALTH']}
def classify(q):
 x=q.lower()
 if any(k in x for k in ('sécur','secur','safety','holdout','mt5','ordre')):return 'SAFETY'
 if any(k in x for k in ('continue','poursui','avance')):return 'CONTINUE'
 if any(k in x for k in ('lacune','gap','capacité','capacite')):return 'CAPABILITY_GAPS'
 if any(k in x for k in ('réflex','reflex','critique')):return 'REFLECTION'
 if any(k in x for k in ('objectif','goal')):return 'GOALS'
 if any(k in x for k in ('agenda','plan','autonom')):return 'AGENDA'
 return 'STATUS'
def plan(q):
 k=classify(q);mid=hashlib.sha256((q+str(time.time_ns())).encode()).hexdigest()[:16]
 return {'schema_version':2,'kind':'JARVIS_MISSION_PLAN_V2','mission_id':mid,'request':q,'mission_kind':k,'steps':PLANS[k],'policy':'ALLOWLIST_ONLY;FAIL_CLOSED;MINIMUM_SUFFICIENT_ACTION','orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
