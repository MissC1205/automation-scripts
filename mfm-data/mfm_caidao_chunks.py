#!/usr/bin/env python3
"""Inspect a small set of public Caidao lazy-page JS assets for read API argument patterns."""
import datetime as dt
import json
import pathlib
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT="http://zk.bjjckx.com"
INDEX=ROOT+"/static/js/index.e98df7de.js"
TZ=ZoneInfo("Asia/Shanghai")
MARKERS=("getSpfzstdetail","getRqSpfzstdetail","getJcZstDetail",
         "getLeagueMatchList","getWorldCupOddsList",
         "footballQuery","getMatchCalculator","matchId","matchNo")
HEADERS={"User-Agent":"MFM-public-JS-source-audit/1.0"}

def fetch(url,cap=3_000_000):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=12) as response:
        data=response.read(cap+1)
        if len(data)>cap:
            raise ValueError("ASSET_SIZE_LIMIT")
        return data.decode("utf-8",errors="replace")

def run():
    src=fetch(INDEX)
    pairs=dict(re.findall(r'"([a-zA-Z][^"]{4,175})":"([0-9a-f]{8})"',src))
    keywords=("football","match","award","zst","odds","simulate-game","sports")
    candidates=[(k,v) for k,v in pairs.items() if any(tag in k.lower() for tag in keywords)]
    # Prefer football/detail and public lottery market pages; do not scan entire app.
    def rank(item):
        name=item[0].lower()
        return (
            0 if "award-detail-football" in name else
            1 if "match-live-football-football-detail" in name else
            2 if "simulate-game" in name else
            3 if "football" in name else
            4 if "award" in name else
            5 if "odds" in name or "zst" in name else 6,
            len(name)
        )
    candidates=sorted(candidates,key=rank)
    out={"captured_at_bj":dt.datetime.now(TZ).isoformat(),
         "candidate_chunk_count":len(candidates),
         "candidate_chunk_names":[x[0] for x in candidates[:85]],
         "reviewed_public_js":[]}
    for name,code in candidates[:14]:
        # Validated from the public webpack runtime's chunk-name/hash mapping.
        url=ROOT+"/static/js/"+urllib.parse.quote(name,safe="~") +"."+code+".js"
        record={"chunk":name,"url":url}
        try:
            js=fetch(url)
            record["bytes"]=len(js.encode())
            snippets=[]
            for marker in MARKERS:
                for hit in list(re.finditer(re.escape(marker),js,flags=re.I))[:5]:
                    context=js[max(0,hit.start()-280):hit.end()+300]
                    context=re.sub(r'(?i)(authorization|password|secret|token)\s*[:=]\s*["\x27][^"\x27]{0,100}',r'[REDACTED]',context)
                    snippets.append({"marker":marker,"context":context[:600]})
            record["matched_callsite_count"]=len(snippets)
            record["contexts"]=snippets[:18]
        except (OSError,ValueError) as exc:
            record["error_type"]=type(exc).__name__
            record["error"]=str(exc)[:180]
        out["reviewed_public_js"].append(record)
    return out

if __name__=="__main__":
    root=pathlib.Path("mfm-data/source-diagnostics")
    root.mkdir(parents=True,exist_ok=True)
    out=run()
    target=root/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_chunks.json")
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"candidates":out["candidate_chunk_count"],"examined":len(out["reviewed_public_js"]),"with_callsite":sum(bool(x.get("matched_callsite_count")) for x in out["reviewed_public_js"])},ensure_ascii=False))
