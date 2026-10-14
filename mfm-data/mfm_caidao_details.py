#!/usr/bin/env python3
"""Source-stamped public Caidao detail contract verification for two known matches.

Tests only documented-by-public-H5 read endpoints with matchInfo identifiers
obtained from public fixture response. No authentication or account bypass.
Saves field availability and counts, not private user content or model predictions.
"""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Asia/Shanghai")
ROOT="http://zk.bjjckx.com"
FIXTURES={"008":{"matchInfo":"F20261014008","teams":"罗马 - 皇马"},
          "011":{"matchInfo":"F20261014011","teams":"曼城 - 巴黎圣曼"}}
ENDPOINTS=(
    "getMatchAllData",
    "getSpfzstdetail",
    "getRqSpfzstdetail",
    "getJcOddsDetail",
)
def request(path,fixture):
    url=ROOT+"/api/web/game/"+path
    form=urllib.parse.urlencode(fixture).encode("utf-8")
    req=urllib.request.Request(url,data=form,headers={
        "User-Agent":"MFM-public-read-only-data-validation/1.0",
        "Referer":ROOT+"/",
        "Accept":"application/json, text/plain, */*",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"},method="POST")
    with urllib.request.urlopen(req,timeout=13) as r:
        data=r.read(1_000_001)
        return r.status,data,len(data)>1_000_000

def data_summary(data):
    out={"data_type":type(data).__name__}
    if isinstance(data,list):
        out["row_count"]=len(data)
        if data and isinstance(data[0],dict):
            out["first_row_keys"]=sorted(data[0])[:75]
    elif isinstance(data,dict):
        out["data_keys"]=sorted(data)[:100]
        out["collection_counts"]={k:len(v) for k,v in data.items() if isinstance(v,list)}
        out["nested_json_string_shapes"]={}
        for k,v in data.items():
            if k.endswith("Str") and isinstance(v,str):
                try:
                    parsed=json.loads(v)
                    out["nested_json_string_shapes"][k]={"kind":type(parsed).__name__,
                         "count":len(parsed) if isinstance(parsed,(dict,list)) else None,
                         "keys":sorted(parsed)[:30] if isinstance(parsed,dict) else []}
                except ValueError:
                    out["nested_json_string_shapes"][k]={"kind":"not_json","length":len(v)}
        # Preserve only small scalar odds-like values with no personal data.
        out["public_scalar_market_values"]={
            k:str(v)[:120] for k,v in data.items()
            if isinstance(v,(int,float,str)) and len(str(v))<120
            and any(term in k.lower() for term in ("odds","spvalue","concedenum","goalline"))
        }
    elif isinstance(data,str):
        out["length"]=len(data)
    return out

def run():
    output={"observed_bj":dt.datetime.now(TZ).isoformat(),
            "source":ROOT,"kind":"public_contract_test_only",
            "valid_match_level_sp_history_confirmed":False,
            "matches":[]}
    for number,fixture in FIXTURES.items():
        match={"match_number":number,"matchInfo":fixture["matchInfo"],
               "teams":fixture["teams"],"endpoints":[]}
        for endpoint in ENDPOINTS:
            item={"endpoint":endpoint,"method":"POST","parameter_keys":["matchInfo"]}
            try:
                http,raw,truncated=request(endpoint,{"matchInfo":fixture["matchInfo"]})
                item.update({"http_status":http,"response_bytes":len(raw),"truncated":truncated})
                if not truncated:
                    response=json.loads(raw)
                    if isinstance(response,dict):
                        item["top_keys"]=sorted(response)[:30]
                        for k in ("status","code","message"):
                            if isinstance(response.get(k),(str,int)):
                                item[k]=str(response[k])[:100]
                        item.update(data_summary(response.get("data")))
            except urllib.error.HTTPError as ex:
                item.update({"http_status":ex.code,"error_type":"HTTPError"})
                if ex.code in (401,403,429,567):
                    match["endpoints"].append(item)
                    match["stopped_due_to_access_restriction"]=True
                    break
            except (OSError,ValueError) as ex:
                item.update({"error_type":type(ex).__name__,"error":str(ex)[:160]})
            match["endpoints"].append(item)
        output["matches"].append(match)
    return output

if __name__=="__main__":
    result=run()
    base=pathlib.Path("mfm-data/source-diagnostics")
    base.mkdir(parents=True,exist_ok=True)
    target=base/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_details.json")
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),
        "coverage":[{"match":m["match_number"],"endpoints":[{"name":e["endpoint"],
         "http":e.get("http_status"),"business_status":e.get("status"),
         "type":e.get("data_type"),"rows":e.get("row_count")} for e in m["endpoints"]]}
         for m in result["matches"]]},ensure_ascii=False))
