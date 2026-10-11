import json,os,urllib.request
ENGINE="V57_JARVIS_LLM_BACKEND_V3_2"
MODEL="openai/gpt-oss-20b"
URL="https://api.groq.com/openai/v1/chat/completions"
def complete(system,user,max_tokens=1200):
    key=os.environ.get("GROQ_API_KEY")
    if not key: raise RuntimeError("GROQ_API_KEY_MISSING")
    body=json.dumps({"model":MODEL,"messages":[{"role":"system","content":str(system)},{"role":"user","content":str(user)}],"max_completion_tokens":int(max_tokens),"include_reasoning":False,"response_format":{"type":"json_object"}}).encode()
    req=urllib.request.Request(URL,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":"TradingAI-JARVIS/3"})
    with urllib.request.urlopen(req,timeout=60) as r: out=json.loads(r.read())
    return {"engine":ENGINE,"model":MODEL,"content":out["choices"][0]["message"]["content"],"orders_allowed":False,"mt5_launch_allowed":False,"mutation_allowed":False,"tool_execution_allowed":False}
