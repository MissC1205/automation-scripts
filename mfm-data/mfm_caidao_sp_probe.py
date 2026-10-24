#!/usr/bin/env python3
"""Limited read-only public SP-history parameter contract checks.

Identifiers are copied from the public match fixture and match-detail fields.
Test only three documented-by-response ID field names, no enumeration,
credentials, access-control bypass, or private response persistence.
"""
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Asia/Shanghai")
ROOT="http://zk.bjjckx.com/api/web/game/"
IDS={"matchInfo":"F20261014008","matchId":"2633781","jcMatchId":"2041968","sportteryMatchId":"2041968"}
PARAMS=(
    {"matchInfo":IDS["matchInfo"]},
    {"matchId":IDS["matchId"]},
    {"jcMatchId":IDS["jcMatchId"]},
    {"sportteryMatchId":IDS["sportteryMatchId"]},
)
def probe(endpoint,values):
    data=urllib.parse.urlencode(values).encode("utf-8")
    req=urllib.request.Request(ROOT+endpoint,data=data,method="POST",headers={
        "User-Agent":"MFM-public-market-contract-audit/1.0",
        "Referer":"http://zk.bjjckx.com/",
        "Accept":"application/json, text/plain, */*",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"})
    with urllib.request.urlopen(req,timeout=12) as response:
        raw=response.read(160001)
        if len(raw)>160000:raise ValueError("RESPONSE_LIMIT")
        return response.status,json.loads(raw)
def summary(payload):
    out={"response_type":type(payload).__name__}
    if not isinstance(payload,dict):return out
    for k in ("status","message","code"):
        if isinstance(payload.get(k),(str,int)):
            out[k]=str(payload[k])[:100]
    value=payload.get("data")
    out["data_type"]=type(value).__name__
    if isinstance(value,(dict,list)):
        out["data_length"]=len(value)
        if isinstance(value,dict):
            out["data_keys"]=sorted(value)[:60]
        elif value and isinstance(value[0],dict):
            out["first_record_keys"]=sorted(value[0])[:60]
    elif isinstance(value,str):
        out["data_string_length"]=len(value)
    return out

def run():
    out={"when_bj":dt.datetime.now(TZ).isoformat(),"fixture":"周三008",
         "source":"public Caidao API","results":[],"verified_history_rows":0}
    for endpoint in ("getJcOddsDetail","getSpfzstdetail","getRqSpfzstdetail"):
        for params in PARAMS:
            info={"endpoint":endpoint,"parameter_keys":list(params)}
            try:
                status,payload=probe(endpoint,params)
                info["http_status"]=status
                info.update(summary(payload))
                if info.get("data_length",0)>0:
                    out["verified_history_rows"]+=info.get("data_length",0)
            except urllib.error.HTTPError as exc:
                info["http_status"]=exc.code
                info["error_type"]="HTTPError"
                if exc.code in (401,403,429,567):
                    out["results"].append(info)
                    out["access_restricted_stop"]=True
                    return out
            except (OSError,ValueError) as exc:
                info["error_type"]=type(exc).__name__
                info["error"]=str(exc)[:120]
            out["results"].append(info)
            time.sleep(.6)
    return out

if __name__=="__main__":
    result=run()
    root=pathlib.Path("mfm-data/source-diagnostics")
    root.mkdir(parents=True,exist_ok=True)
    target=root/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_sp_history.json")
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"tests":len(result["results"]),
                      "nonempty_shapes":sum(bool(x.get("data_length")) for x in result["results"])},ensure_ascii=False))
