#!/usr/bin/env python3
"""Small public read-only contract test for integer-handicap odds history.

Only candidate 'wf' market values supported by public H5 market labels;
two known fixture IDs, no auth, no access-control bypass or token probing.
"""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT="http://zk.bjjckx.com/api/web/game/getJcOddsDetail"
TZ=ZoneInfo("Asia/Shanghai")
FIXTURES={"008":"F20261014008","011":"F20261014011"}
MARKETS=("spf","rqspf")
def post(params):
    req=urllib.request.Request(ROOT,data=urllib.parse.urlencode(params).encode(),
       headers={"User-Agent":"MFM-public-market-contract-probe/1.0",
                "Referer":"http://zk.bjjckx.com/",
                "Accept":"application/json",
                "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"},
       method="POST")
    with urllib.request.urlopen(req,timeout=12) as r:
        data=r.read(150_001)
    if len(data)>150_000:raise ValueError("EXCESSIVE_PUBLIC_RESPONSE")
    return json.loads(data)
def main():
    result={"observed_bj":dt.datetime.now(TZ).isoformat(),
            "source":"Caidao public H5",
            "market_semantics_not_assumed":True,
            "results":[]}
    for no,identifier in FIXTURES.items():
        for wf in MARKETS:
            entry={"match":no,"matchInfo":identifier,"request_wf":wf}
            try:
                data=post({"matchInfo":identifier,"wf":wf})
                entry["status"]=data.get("status")
                obj=data.get("result")
                if isinstance(obj,dict):
                    entry["returned_wf"]=obj.get("wf")
                    entry["returned_handicap"]=obj.get("concedeNum")
                    rows=obj.get("oddsDetails")
                    if isinstance(rows,list):
                        entry["row_count"]=len(rows)
                        entry["first_and_last"]=[
                           {k:r.get(k) for k in ("updateTime","odds")}
                           for r in ([rows[0],rows[-1]] if len(rows)>1 else rows)
                           if isinstance(r,dict)]
                entry["has_valid_handicap_history"]=wf=="rqspf" and entry.get("returned_wf")=="rqspf" and entry.get("row_count",0)>0
            except urllib.error.HTTPError as e:
                entry["http_status"]=e.code
                if e.code in (401,403,429,567):
                    result["results"].append(entry)
                    result["access_restricted_stop"]=True
                    break
            except (OSError,ValueError) as e:
                entry["error_type"]=type(e).__name__
                entry["error"]=str(e)[:130]
            result["results"].append(entry)
        if result.get("access_restricted_stop"):break
    output=pathlib.Path("mfm-data/source-diagnostics")
    output.mkdir(parents=True,exist_ok=True)
    target=output/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_handicap_probe.json")
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"results":result["results"]},ensure_ascii=False))
if __name__=="__main__":
    main()
