#!/usr/bin/env python3
"""Check real Caidao public match-list calls using arguments found in H5 JS.

No authentication, no scraping around access controls, no bulk data collection.
Save only public fixture fields and aggregate response information; do not save
any account, internal prediction, or paid content.
"""
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Asia/Shanghai")
BASE="http://zk.bjjckx.com/api/web/game/footballQuery"
ALLOWED=("matchNum","matchInfo","matchName","hostTeam","guestTeam",
         "homeTeam","awayTeam","homeTeamShortName","awayTeamShortName",
         "gameTime","matchDate","status","gameStatus","score","id")

def request(query):
    url=BASE+"?"+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={
        "User-Agent":"MFM-public-football-data-check/1.0",
        "Accept":"application/json, text/plain, */*",
        "Referer":"http://zk.bjjckx.com/"},method="GET")
    with urllib.request.urlopen(req,timeout=12) as response:
        raw=response.read(1_000_001)
        return response.status,raw,len(raw)>1_000_000

def observe():
    output={"observed_bj":dt.datetime.now(TZ).isoformat(),
            "endpoint":"GET /api/web/game/footballQuery",
            "calls":[],"source":"caidao-public-H5",
            "complete_daily_fixture_coverage_verified":False}
    # Exact type argument from public Vue getMatchList(). No valid userId
    # is available when browsing anonymously; test omitted/anonymous ID.
    scenarios=[{"type":0},{"type":1},{"type":0,"userId":0}]
    for params in scenarios:
        entry={"params":params}
        try:
            status,raw,truncated=request(params)
            entry.update({"http_status":status,"bytes":len(raw),"truncated":truncated})
            if truncated:
                entry["parse_status"]="RESPONSE_TOO_LARGE"
            else:
                payload=json.loads(raw)
                entry["json_type"]=type(payload).__name__
                if isinstance(payload,dict):
                    entry["keys"]=sorted(payload.keys())[:25]
                    for k in ("code","status","message"):
                        if isinstance(payload.get(k),(int,str)):
                            entry[k]=str(payload[k])[:120]
                    body=payload.get("body")
                    entry["body_type"]=type(body).__name__
                    if isinstance(body,list):
                        entry["body_rows"]=len(body)
                        entry["public_fixtures"]=[
                            {k:r[k] for k in ALLOWED if k in r and isinstance(r[k],(str,int,float))}
                            for r in body[:120] if isinstance(r,dict)
                        ]
                        entry["public_fixture_keys_first"]=sorted(body[0])[:55] if body and isinstance(body[0],dict) else []
                    elif isinstance(body,dict):
                        entry["body_keys"]=sorted(body)[:55]
                        entry["nested_list_counts"]={k:len(v) for k,v in body.items() if isinstance(v,list)}
        except urllib.error.HTTPError as exc:
            entry["http_status"]=exc.code
            entry["error_type"]="HTTPError"
            if exc.code in (401,403,429,567):
                output["calls"].append(entry)
                output["status"]="ACCESS_RESTRICTED_STOPPED"
                break
        except (OSError,ValueError) as exc:
            entry["error_type"]=type(exc).__name__
            entry["error"]=str(exc)[:220]
        output["calls"].append(entry)
    return output

if __name__=="__main__":
    result=observe()
    root=pathlib.Path("mfm-data/source-diagnostics")
    root.mkdir(parents=True,exist_ok=True)
    file=root/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_fixtures.json")
    file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(file),"calls":[{"params":c["params"],"http":c.get("http_status"),"body_rows":c.get("body_rows"),"error":c.get("error_type")} for c in result["calls"]]},ensure_ascii=False))
