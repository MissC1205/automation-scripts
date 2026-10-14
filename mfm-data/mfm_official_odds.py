#!/usr/bin/env python3
"""Hourly official odds probe. Never substitutes third-party quotes for official SP."""
import datetime as dt, json, os, pathlib, urllib.request, urllib.error, subprocess
from zoneinfo import ZoneInfo
TZ=ZoneInfo("Asia/Shanghai")
now=dt.datetime.now(TZ)
base=pathlib.Path("mfm-data/official-odds")/now.strftime("%Y-%m-%d")
base.mkdir(parents=True,exist_ok=True)
urls={
 "calculator":"https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry",
 "history":"https://webapi.sporttery.cn/gateway/uniform/football/getOddsHistoryV1.qry",
}
out={"collected_at":now.isoformat(),"source":"sporttery.cn","official_sale_list_verified":False,"sources":{},"matches":[],"status":"unverified"}
for name,url in urls.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"MFM-odds-audit/1.0","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=12) as r:
   raw=r.read(3000000)
   value=json.loads(raw)
   out["sources"][name]={"http_status":r.status,"retrieved_at":dt.datetime.now(TZ).isoformat(),"url":url,"payload":value}
 except Exception as e:
  out["sources"][name]={"url":url,"error_type":type(e).__name__,"error":str(e)[:240],"retrieved_at":dt.datetime.now(TZ).isoformat()}
# Preserve raw responses, including errors. Do not infer match schema or publish invented SP.
if all("payload" in v for v in out["sources"].values()):
 out["status"]="raw_responses_available_requires_schema_validation"
else:
 out["status"]="source_failure"
path=base/(now.strftime("%Y%m%dT%H%M%S%z")+".json")
path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"file":str(path),"status":out["status"],"source_states":{k:("ok" if "payload" in v else v["error_type"]) for k,v in out["sources"].items()}},ensure_ascii=False))
