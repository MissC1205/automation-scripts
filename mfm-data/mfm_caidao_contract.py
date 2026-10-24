#!/usr/bin/env python3
"""Read-only reverse documentation of Caidao's publicly served JS for MFM.

Inspects static H5 JavaScript only; never guesses credentials or calls private
endpoints. Extracts public endpoint method signatures and page call sites.
"""
import datetime as dt
import json
import pathlib
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

BASE="http://zk.bjjckx.com"
INDEX=BASE+"/static/js/index.e98df7de.js"
TZ=ZoneInfo("Asia/Shanghai")
HDR={"User-Agent":"MFM-public-contract-inspection/1.0","Accept":"application/javascript,*/*"}
TOKENS=[
    "getSpfzstdetail","getRqSpfzstdetail","getJcZstDetail",
    "getLeagueMatchList","getWorldCupOddsList","footballQuery","footballLiveQuery",
    "matchNum","matchId","matchNo","issueNo","matchInfo","leagueMatch","matchDate",
    "spfList","hadList","getOdds","oddsHistory","spHistory","getSchedule",
    "getMatchList","gameId","scheduleId","matchCode","赛事","胜平负","sp值",
]
REDACT=re.compile(r'(?i)(password|authorization|access_token|refresh_token|api[-_]?key|secret)\s*[:=]\s*["\x27][^"\x27]{0,150}')
def grab(url):
    req=urllib.request.Request(url,headers=HDR)
    with urllib.request.urlopen(req,timeout=16) as f:
        data=f.read(3_000_001)
    if len(data)>3_000_000:raise ValueError("JS_TOO_BIG")
    return data.decode("utf-8",errors="replace")
def inspect():
    index=grab(INDEX)
    matches=dict(re.findall(r'"([^"]{4,175})":"([a-f0-9]{8})"',index))
    names=[key for key in matches if any(x in key.lower() for x in ("football","match","award","simulation","simulate-game","schedule","odds","sporttery"))]
    names=sorted(names,key=lambda s:(0 if "football-detail" in s else 1 if "match" in s else 2,len(s)))
    out={"observed_at_bj":dt.datetime.now(TZ).isoformat(),
         "source_index":INDEX,"found_candidate_chunks":len(names),
         "chunks":[],"public_assets_only":True}
    for chunk in ["INDEX"]+names[:27]:
        if chunk=="INDEX":
            js=index
            url=INDEX
        else:
            url=BASE+"/static/js/"+urllib.parse.quote(chunk,safe="~")+"."+matches[chunk]+".js"
            try:js=grab(url)
            except Exception as e:
                out["chunks"].append({"chunk":chunk,"url":url,"error":str(e)[:180]})
                continue
        found={}
        for token in TOKENS:
            hits=list(re.finditer(re.escape(token),js,re.I))
            if not hits:continue
            snippets=[]
            for h in hits[:(4 if token.startswith("get") or token in ("footballQuery","footballLiveQuery") else 2)]:
                pre=260 if token.startswith("get") else 120
                post=280 if token.startswith("get") else 170
                s=js[max(0,h.start()-pre):min(len(js),h.end()+post)]
                s=REDACT.sub("[REDACTED]",s)
                snippets.append({"offset":h.start(),"around":s[:600]})
            found[token]={"count":len(hits),"contexts":snippets}
        out["chunks"].append({"chunk":chunk,"url":url,"len_js":len(js),"tokens":found})
    return out
if __name__=="__main__":
    result=inspect()
    dest=pathlib.Path("mfm-data/source-diagnostics")
    dest.mkdir(parents=True,exist_ok=True)
    path=dest/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_contract.json")
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(path),"chunks":len(result["chunks"]),
       "chunks_containing_sp_history":sum("getSpfzstdetail" in x.get("tokens",{}) for x in result["chunks"]),
       "chunks_containing_football_query":sum("footballQuery" in x.get("tokens",{}) for x in result["chunks"])}))
