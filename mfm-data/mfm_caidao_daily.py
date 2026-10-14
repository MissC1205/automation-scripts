#!/usr/bin/env python3
"""MFM Caidao publicly accessible DAILY coverage audit (not a prediction).

Only two H5-observed public read endpoints, no credentials or paid content.
Never publishes provider narrative, other-user content or third-party picks.
Source-stamped, pre/post kickoff distinguished to avoid lookahead leakage.
"""
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Asia/Shanghai")
ROOT="http://zk.bjjckx.com"
DATE=dt.datetime.now(TZ).date().isoformat()
MATCH_ID_PREFIX="F"+DATE.replace("-","")
MARKETS=("spfOdds","rqspfOdds","concedeNum","bfOdds","zjqOdds","bqcOdds")
STRUCTURES=("historyDataStr","matchFeatureStr","injurySuspensionStr",
            "okMatchDataStr","poissonDistributionStr","matchTableStr",
            "matchTableDetailStr","ttylIndexStr","ttylWhoScoredStr")
HEADERS={"User-Agent":"MFM-public-coverage-audit/1.0",
         "Accept":"application/json, text/plain, */*",
         "Referer":ROOT+"/"}
def call(path,params,method="GET"):
    url=ROOT+path
    body=None
    if method=="GET":url+="?"+urllib.parse.urlencode(params)
    else:body=urllib.parse.urlencode(params).encode("utf-8")
    headers=dict(HEADERS)
    if body is not None:headers["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8"
    request=urllib.request.Request(url,headers=headers,data=body,method=method)
    with urllib.request.urlopen(request,timeout=16) as resp:
        raw=resp.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError("PUBLIC_RESPONSE_EXCEEDS_2MB")
        return json.loads(raw)

def market_summary(raw):
    result={}
    for key in MARKETS:
        value=raw.get(key)
        field={"kind":type(value).__name__,"nonempty":value is not None and value!="" and value!=[]}
        # Capture small public market values only; never account data.
        if isinstance(value,(int,float)) or isinstance(value,str) and len(value)<350:
            field["published_value"]=value
        elif isinstance(value,list):
            field["length"]=len(value)
            field["numeric_head"]=[n for n in value[:12] if isinstance(n,(int,float))]
        result[key]=field
    return result

def schema_summary(key,val):
    result={"present":val is not None and val!="","type":type(val).__name__}
    if isinstance(val,str) and val:
        try:val=json.loads(val)
        except (ValueError,TypeError):
            result["parse_error"]=True;return result
    result["parsed_type"]=type(val).__name__
    if isinstance(val,(dict,list)):
        result["item_count"]=len(val)
    if isinstance(val,dict):
        result["keys"]=sorted(val)[:50]
        if key=="historyDataStr":
            matches=val.get("matchList")
            result["history_match_count"]=len(matches) if isinstance(matches,list) else None
        if key=="injurySuspensionStr":
            result["injury_counts"]={t:len(v) if isinstance(v,list) else
                len(v) if isinstance(v,dict) else None for t,v in val.items() if t in ("home","away")}
        if key=="matchFeatureStr":
            result["numeric_leaves"]={k:v for k,v in val.items() if isinstance(v,(int,float))}
            result["metric_shapes"]={k:{"type":type(v).__name__,"length":len(v) if isinstance(v,(list,dict)) else None}
                   for k,v in val.items() if k in ("last","goalAvg","lossGoalAvg","eachHomeAway","sameHomeAway")}
        if key=="okMatchDataStr":
            result["team_strength_values"]={k:v for k,v in val.items() if k in ("home_value","away_value") and isinstance(v,(float,int))}
    return result

def main():
    now=dt.datetime.now(TZ)
    result={"date":DATE,"collected_at_bj":now.isoformat(),
            "source":ROOT,"source_class":"third_party_aggregator_not_official_JC",
            "data_is_provider_reported_not_independently_verified":True,
            "third_party_poisson_results_excluded_from_independent_model":True,
            "lookahead_rule":"kickoff_at <= collected_at marks POST_KICKOFF; cannot use as prematch-only dataset",
            "coverage":{},"matches":[]}
    raw=[]
    for typ in (0,1):
        try:
            payload=call("/api/web/game/footballQuery",{"type":typ})
            body=payload.get("body") if isinstance(payload,dict) else None
            body=body if isinstance(body,list) else []
            filtered=[a for a in body if isinstance(a,dict) and str(a.get("matchInfo","")).startswith(MATCH_ID_PREFIX)]
            result["coverage"]["type_"+str(typ)]={"api_status":payload.get("status"),"total_rows":len(body),"today_rows":len(filtered)}
            raw.extend(filtered)
        except (OSError,ValueError) as ex:
            result["coverage"]["type_"+str(typ)]={"error_type":type(ex).__name__,"error":str(ex)[:180]}
        time.sleep(.5)
    unique={}
    for row in raw:
        ident=row.get("matchInfo")
        if ident:unique[ident]=row
    result["coverage"]["unique_today_match_ids"]=len(unique)
    for ident,row in sorted(unique.items()):
        day=row.get("gameTime")
        try:
            kickoff=dt.datetime.strptime(str(day),"%Y%m%d%H%M%S").replace(tzinfo=TZ)
            time_class="POST_KICKOFF" if kickoff<=now else "PRE_KICKOFF"
            kickoff_at=kickoff.isoformat()
        except ValueError:
            time_class="UNKNOWN";kickoff_at=None
        match={"match_id":ident,"jc_number_display":row.get("matchNum"),
               "home":row.get("hostTeam"),"away":row.get("guestTeam"),
               "competition":row.get("matchName"),"kickoff_bj":kickoff_at,
               "time_class":time_class,"match_status":row.get("gameStatus"),
               "markets":market_summary(row)}
        try:
            response=call("/api/web/game/getMatchAllData",{"matchInfo":ident},"POST")
            match["detail_business_status"]=response.get("status")
            data=response.get("data")
            match["detail_data_type"]=type(data).__name__
            if isinstance(data,dict):
                match["detail_fields_present"]=sorted(k for k,v in data.items() if v not in (None,"",[],{}))
                match["feature_schemas"]={k:schema_summary(k,data.get(k)) for k in STRUCTURES}
                match["provider_update_time"]=data.get("updateTime")
            else:
                match["detail_fields_present"]=[]
        except urllib.error.HTTPError as ex:
            match["detail_error"]={"type":"HTTPError","status":ex.code}
            if ex.code in (401,403,429,567):
                result["coverage"]["access_restricted_stop"]=True
                result["matches"].append(match)
                break
        except (OSError,ValueError) as ex:
            match["detail_error"]={"type":type(ex).__name__,"message":str(ex)[:140]}
        result["matches"].append(match)
        time.sleep(.6)
    result["coverage"]["detail_success_count"]=sum(isinstance(m.get("feature_schemas"),dict) for m in result["matches"])
    result["coverage"]["pre_kickoff_detail_count"]=sum(m["time_class"]=="PRE_KICKOFF" and isinstance(m.get("feature_schemas"),dict) for m in result["matches"])
    result["coverage"]["post_kickoff_detail_count"]=sum(m["time_class"]=="POST_KICKOFF" and isinstance(m.get("feature_schemas"),dict) for m in result["matches"])
    root=pathlib.Path("mfm-data/caidao-coverage")
    root.mkdir(parents=True,exist_ok=True)
    target=root/(DATE+"-"+now.strftime("%H%M%S")+".json")
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"coverage":result["coverage"],
        "match_numbers":[m.get("jc_number_display") for m in result["matches"]]},ensure_ascii=False))

if __name__=="__main__":main()
