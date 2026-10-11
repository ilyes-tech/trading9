import json,re
import v57_llm_backend_v3_2 as LLM
ENGINE="V57_JARVIS_CRITIC_V3_3"
FORBIDDEN=("mt5","order_send","broker","live order","holdout","september 2026","subprocess","os.system","shell command")
SYSTEM="You are a scientific critic. Use development data only. Never request MT5, broker access, orders, holdout data, September 2026 data, file mutation, tools, commands, or execution. Return ONLY valid JSON with keys weakness,test,expected_observation,rejection_condition."
def critique(hypothesis,max_tokens=1000):
    if not str(hypothesis).strip(): raise ValueError("EMPTY_HYPOTHESIS")
    r=LLM.complete(SYSTEM,str(hypothesis),max_tokens)
    raw=r["content"].strip()
    if not raw: raise ValueError("CRITIC_EMPTY_RESPONSE")
    if raw.startswith("```"): raw=re.sub(r"^```(?:json)?\\s*|\\s*```$","",raw,flags=re.I|re.S).strip()
    try: d=json.loads(raw)
    except Exception as e: raise ValueError("CRITIC_INVALID_JSON") from e
    required=("weakness","test","expected_observation","rejection_condition")
    if set(d)!=set(required) or any(not isinstance(d[k],str) or not d[k].strip() for k in required): raise ValueError("CRITIC_BAD_SCHEMA")
    text=" ".join(d.values()).lower()
    bad=[x for x in FORBIDDEN if x in text]
    if bad: raise ValueError("CRITIC_FORBIDDEN_CONTENT:"+",".join(bad))
    return {"engine":ENGINE,"status":"PROPOSAL_ONLY","critique":d,"orders_allowed":False,"mt5_launch_allowed":False,"mutation_allowed":False,"tool_execution_allowed":False,"promotion_allowed":False}
