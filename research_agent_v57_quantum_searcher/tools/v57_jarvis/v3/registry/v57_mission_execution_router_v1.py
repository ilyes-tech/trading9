import importlib.util,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
def _load(n,a):
 s=importlib.util.spec_from_file_location(a,HERE/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
PROJECT=_load('v57_general_readonly_adapter_v1.py','j57projectro')
PROJECT_WORDS=('projet','tradingai','jarvis','état','etat','où en sommes','ou en sommes','priorité','priorite')
SAFE_PATTERNS=(r"n['’]ex[ée]cute\s+aucune\s+modification",r"n['’]ex[ée]cute\s+aucune\s+action(?:\s+de\s+march[ée])?",r"ne\s+modifie\s+rien",r"sans\s+(?:faire\s+de\s+)?modification",r"sans\s+ex[ée]cuter\s+(?:d['’])?action(?:\s+de\s+march[ée])?",r"(?:en\s+)?lecture\s+seule",r"read[- ]only")
MUTATING_PATTERNS=(r'\bmodifi(?:e|er)\b',r'\bsupprim(?:e|er)\b',r'\binstall(?:e|er)\b',r'\bex[ée]cut(?:e|er)\b',r'\br[ée]par(?:e|er)\b',r'\bcr[ée](?:e|er)\b',r'\bd[ée]plac(?:e|er)\b',r'\bkill\b')
def classify(text):
 q=' '.join(str(text).strip().split());low=q.lower()
 if not q:return 'EMPTY',q,low
 sanitized=low
 for p in SAFE_PATTERNS:sanitized=re.sub(p,' ',sanitized)
 if any(re.search(p,sanitized) for p in MUTATING_PATTERNS):return 'MUTATING',q,low
 if any(k in low for k in PROJECT_WORDS):return 'PROJECT_READONLY',q,low
 return 'UNKNOWN',q,low
def route(text, classified_readonly=False):
 q=' '.join(str(text).strip().split())
 base={'orders_allowed':False,'mt5_launch_allowed':False,'holdout_allowed':False,'promotion_allowed':False}
 if classified_readonly:return PROJECT.execute_classified_readonly(q)
 kind,q,_=classify(q)
 if kind=='PROJECT_READONLY':return PROJECT.execute(q)
 if kind=='MUTATING':return dict(base,status='REFUSED',route='MISSION_EXECUTION',reason='MUTATING_CAPABILITY_NOT_ALLOWED_V1',answer='Mission Execution V1 est en lecture seule; aucune modification exécutée.')
 return dict(base,status='REFUSED',route='MISSION_EXECUTION',reason='EMPTY_REQUEST' if kind=='EMPTY' else 'NO_SAFE_CAPABILITY_MATCH',answer='Aucune capacité read-only vérifiée ne couvre encore cette mission; aucune action exécutée.')
