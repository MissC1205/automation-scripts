#!/usr/bin/env python3
"""Bounded, unauthenticated Caidao handicap history contract verification.

Read-only methods and match IDs were found in publicly served H5 and fixture
responses. Check response structures only; never guess authentication or
attempt to bypass a denied/paid feature.
"""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT="http://zk.bjjckx.com/api/web/game/"
TZ=ZoneInfo("Asia/Shanghai")
FIXTURES={"008":"F20261014008","011":"F20261014011"}
# A very limited examination of the two likely names for the public
# handicap market. No credentialed endpoints, no range/enumeration probing.
VARIANTS=[
    ("getJcOddsDetail",{"wf":"rqspf"}),
    ("getJcOddsDetail",{"wf":"hhad"}),
    ("getJcOddsDetail",{"type":"rqspf"}),
    ("getRqSpfzstdetail",{"wf":"rqspf"}),
]
def probe(endpoint,info):
    data=urllib.parse.urlencode(info).encode()
    req=urllib.request.Request(ROOT+endpoint,data=data,method="POST",headers={
        "User-Agent":"MFM-public-SP-handicap-contract-check/1.0",
        "Referer":"http://zk.bjjckx.com/",
        "Accept":"application/json, text/plain, */*",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"})
    with urllib.request.urlopen(req,timeout=12) as f:
        raw=f.read(500_001)
        if len(raw)>500_000:raise ValueError("PUBLIC_RESPONSE_SIZE_LIMIT")
    return json.loads(raw)
def run():
    report={"collected_at_bj":dt.datetime.now(TZ).isoformat(),
            "kind":"public_contract_probe_not_validated_handicap_history",
            "tests":[],"handicap_history_verified":False}
    for number,matchid in FIXTURES.items():
        for endpoint,variation in VARIANTS:
            row={"match":number,"endpoint":endpoint,
                 "request_fields":{"matchInfo":matchid,**variation}}
            try:
                response=probe(endpoint,row["request_fields"])
                row["business_status"]=response.get("status")
                row["message"]=str(response.get("message",""))[:80]
                data=response.get("result",response.get("data"))
                row["data_type"]=type(data).__name__
                if isinstance(data,dict):
                    row["result_keys"]=sorted(data)[:35]
                    row["source_market"]=data.get("wf")
                    row["source_handicap"]=data.get("concedeNum")
                    records=data.get("oddsDetails")
                    if isinstance(records,list):
                        row["history_count"]=len(records)
                        row["head_shape"]=sorted(records[0]) if records and isinstance(records[0],dict) else []
                        row["sample_market_odds"]=[
                            {"time":x.get("updateTime"),"odds":x.get("odds")}
                            for x in records[:3] if isinstance(x,dict)]
                        if row["source_market"] in ("rqspf","hhad") and records:
                            report["handicap_history_verified"]=True
                elif isinstance(data,list):row["history_count"]=len(data)
            except urllib.error.HTTPError as e:
                row["http_status"]=e.code
                if e.code in (401,403,429,567):
                    row["stop_reason"]="ACCESS_RESTRICTED"
                    report["tests"].append(row)
                    return report
            except (OSError,ValueError) as e:
                row["error_type"]=type(e).__name__
                row["error"]=str(e)[:120]
            report["tests"].append(row)
    return report

if __name__=="__main__":
    root=pathlib.Path("mfm-data/source-diagnostics")
    root.mkdir(parents=True,exist_ok=True)
    report=run()
    path=root/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_handicap.json")
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(path),"verified":report["handicap_history_verified"],
        "tests":[{"match":r["match"],"endpoint":r["endpoint"],
          "source_market":r.get("source_market"),"rows":r.get("history_count"),
          "status":r.get("business_status"),"http":r.get("http_status")} for r in report["tests"]]},
        ensure_ascii=False))
