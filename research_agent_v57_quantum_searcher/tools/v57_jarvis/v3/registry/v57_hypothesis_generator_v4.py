import hashlib,re
ENGINE="V57_JARVIS_HYPOTHESIS_GENERATOR_V4"
MARKETS=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
TIMEFRAMES=("M5","M15","M30","H1")
SIDES=("LONG","SHORT")
FAMILIES=("momentum","trend","volatility","volume","time","price_action")
def parse(text):
    raw=str(text).strip(); up=raw.upper()
    if not raw: raise ValueError("EMPTY_HYPOTHESIS")
    markets=[x for x in MARKETS if re.search(r"(?<![A-Z0-9])"+re.escape(x)+r"(?![A-Z0-9])",up)]
    tfs=[x for x in TIMEFRAMES if re.search(r"(?<![A-Z0-9])"+re.escape(x)+r"(?![A-Z0-9])",up)]
    sides=[x for x in SIDES if re.search(r"(?<![A-Z0-9])"+x+r"(?![A-Z0-9])",up)]
    fam=[x for x in FAMILIES if re.search(r"(?<![a-z])"+x+r"(?![a-z])",raw.lower())]
    if len(markets)>1: raise ValueError("AMBIGUOUS_MARKET")
    if len(tfs)>1: raise ValueError("AMBIGUOUS_TIMEFRAME")
    if len(sides)>1: raise ValueError("AMBIGUOUS_SIDE")
    canon="|".join([markets[0] if markets else "*",tfs[0] if tfs else "*",sides[0] if sides else "*",",".join(fam) if fam else "*",raw])
    return {"engine":ENGINE,"hypothesis":raw,"market":markets[0] if markets else None,"timeframe":tfs[0] if tfs else None,"side":sides[0] if sides else None,"families":fam,"hypothesis_id":hashlib.sha256(canon.encode()).hexdigest(),"research_only":True,"orders_allowed":False,"mt5_launch_allowed":False,"holdout_allowed":False}
