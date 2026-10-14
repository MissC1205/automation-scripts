#!/usr/bin/env python3
"""Read-only public odds result-shape and page-callsite audit for Caidao.

Uses exactly two independently observed fixture IDs. No account credentials,
no evasion, no persistence of provider user data or proprietary JS bundles.
"""
import datetime as dt
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT="http://zk.bjjckx.com"
TZ=ZoneInfo("Asia/Shanghai")
MATCHES={"008":"F20261014008","011":"F20261014011"}
TARGETS=("getJcOddsDetail",)
JS_INDEX=ROOT+"/static/js/index.e98df7de.js"
KEYWORDS=("football","match","award","jczq","jc-","lottery","data","analyse","analysis","index","odd","trend","zst")
TOKENS=("getJcOddsDetail","getSpfzstdetail","getRqSpfzstdetail",
        "getMatchAllData","getJcDetail","getOddsHistory","getSpf")
HEAD={"User-Agent":"MFM-public-source-field-inspection/1.0",
      "Referer":ROOT+"/","Accept":"application/json, text/plain, */*"}
def request(url,fields=None):
    headers=dict(HEAD)
    body=None
    if fields is not None:
        body=urllib.parse.urlencode(fields).encode()
        headers["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8"
    req=urllib.request.Request(url,data=body,headers=headers,method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req,timeout=13) as response:
        data=response.read(2_000_001)
        if len(data)>2_000_000:raise ValueError("PUBLIC_RESPONSE_SIZE_LIMIT")
        return data
def summarize(v,depth=0):
    if isinstance(v,list):
        out={"type":"list","count":len(v)}
        if v and depth<2:out["first_item_shape"]=summarize(v[0],depth+1)
        return out
    if isinstance(v,dict):
        out={"type":"dict","keys":sorted(v)[:80]}
        if depth<2:
            out["subfields"]={k:summarize(val,depth+1) for k,val in v.items()
                              if isinstance(val,(list,dict)) and not any(x in k.lower()
                                for x in ("user","phone","customer","person","account","token"))}
        return out
    if isinstance(v,str):
        obj={"type":"str","length":len(v)}
        if v and depth<2:
            try:obj["parsed_json"]=summarize(json.loads(v),depth+1)
            except ValueError:pass
        return obj
    return {"type":type(v).__name__}
def run():
    out={"time_bj":dt.datetime.now(TZ).isoformat(),
         "purpose":"public market response shape and observed front-end call sites",
         "odds":{"tested_matches":list(MATCHES),"requests":[]},"chunks":[],
         "public_assets_only":True,"history_rows_verified":0}
    for number,match_info in MATCHES.items():
        for endpoint in TARGETS:
            row={"match":number,"matchInfo":match_info,"endpoint":endpoint}
            try:
                raw=request(ROOT+"/api/web/game/"+endpoint,{"matchInfo":match_info})
                payload=json.loads(raw)
                row["response_bytes"]=len(raw)
                row["status"]=payload.get("status")
                row["message"]=str(payload.get("message",""))[:60]
                row["result_shape"]=summarize(payload.get("result"))
                res=payload.get("result")
                if isinstance(res,dict):
                    row["market_type_source"]=res.get("wf")
                    row["integer_handicap_source"]=res.get("concedeNum")
                    if isinstance(res.get("oddsDetails"),list):
                        row["public_history_entries"]=[
                            {k:v for k,v in e.items()
                             if k in ("num","odds","oddsflag","updateTime")
                             and isinstance(v,(str,int,float))}
                            for e in res["oddsDetails"][:35] if isinstance(e,dict)]
                row["data_shape"]=summarize(payload.get("data"))
                # The source returns market rows as 'result' on some routes,
                # never count the mere presence of a result key as SP history.
            except (OSError,ValueError) as e:
                row["error_type"]=type(e).__name__
                row["error"]=str(e)[:120]
            out["odds"]["requests"].append(row)
    try:
        index=request(JS_INDEX).decode("utf-8",errors="replace")
        chunks=dict(re.findall(r'"([^"]{4,175})":"([a-f0-9]{8})"',index))
        selected=[(name,hashcode) for name,hashcode in chunks.items()
                  if any(word in name.lower() for word in KEYWORDS)]
        selected=sorted(selected,key=lambda x:(0 if "football" in x[0] else 1
                   if "award" in x[0] else 2 if "jc-" in x[0] or "jczq" in x[0] else 3,len(x[0])))
        out["chunk_candidates_total"]=len(selected)
        out["first_candidates"]=[x[0] for x in selected[:90]]
        # Small, bounded public asset inspection; no bulk crawling.
        for name,hashcode in selected[35:70]:
            url=ROOT+"/static/js/"+urllib.parse.quote(name,safe="~")+"."+hashcode+".js"
            item={"name":name,"url":url}
            try:
                js=request(url).decode("utf-8",errors="replace")
                item["bytes"]=len(js)
                contexts={}
                for marker in TOKENS:
                    hits=list(re.finditer(re.escape(marker),js,re.I))
                    if hits:
                        contexts[marker]=[
                            js[max(0,h.start()-220):min(len(js),h.end()+330)][:600]
                            for h in hits[:3]]
                item["references"]=contexts
            except (OSError,ValueError) as e:
                item["error"]=str(e)[:120]
            out["chunks"].append(item)
    except (OSError,ValueError) as e:
        out["public_js_error"]=str(e)[:120]
    return out
if __name__=="__main__":
    report=run()
    folder=pathlib.Path("mfm-data/source-diagnostics")
    folder.mkdir(parents=True,exist_ok=True)
    target=folder/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_odds_structure.json")
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"markets":[{"match":r["match"],
        "result_shape":r.get("result_shape"),"status":r.get("status")} for r in report["odds"]["requests"]],
        "chunks":len(report["chunks"]),"callsite_found":sum(bool(x.get("references")) for x in report["chunks"])},
        ensure_ascii=False))
