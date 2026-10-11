"""Research-only Crossref bibliography discovery; never admits hypotheses or runs strategies."""
import argparse,json,urllib.parse,urllib.request

def discover(query,limit=5):
    if not query.strip() or not 1<=limit<=10: raise ValueError('INVALID_QUERY_OR_LIMIT')
    url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.bibliographic':query,'rows':limit,'select':'DOI,title,published,author,URL,type'})
    req=urllib.request.Request(url,headers={'User-Agent':'TradingAI-JARVIS-Research/1.0 (bibliography-only)','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=12) as response:
        data=json.load(response)
    result=[]
    for item in data.get('message',{}).get('items',[]):
        doi=item.get('DOI','');title=item.get('title',['']);published=item.get('published',{}).get('date-parts',[])
        result.append({'doi':doi,'title':title[0] if title else '', 'published':published[0] if published else [],'url':item.get('URL',''),'type':item.get('type','')})
    return {'kind':'V57_LITERATURE_DISCOVERY_V1','status':'BIBLIOGRAPHY_ONLY','query':query,'results':result,'novelty_proven':False,'independent_replication_proven':False,'research_execution_authorized':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--query',required=True);p.add_argument('--limit',type=int,default=5);a=p.parse_args()
    try: print(json.dumps(discover(a.query,a.limit),ensure_ascii=False,indent=2))
    except Exception as e: print('STOP|FAIL|LITERATURE_DISCOVERY|'+type(e).__name__+':'+str(e));raise SystemExit(2)
