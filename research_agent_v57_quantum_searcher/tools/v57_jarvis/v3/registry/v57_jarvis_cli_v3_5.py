import json,sys
import v57_reason_act_v3_5 as J
def show(r):
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))
if len(sys.argv)>1:
    show(J.ask(" ".join(sys.argv[1:])))
    raise SystemExit(0)
print("JARVIS V3")
print("Je vous écoute.")
while True:
    try: q=input("> ").strip()
    except (EOFError,KeyboardInterrupt): break
    if q.lower() in ("exit","quit","quitter"): break
    if q: show(J.ask(q))
