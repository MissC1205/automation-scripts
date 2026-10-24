#!/usr/bin/env python3
"""Collect public Caidao SPF historical snapshots for a single JC sale date.

Read-only endpoints visible in the public H5 application. No credentials, no
access bypass, no third-party predictions. Treat prices as *Caidao-reported*,
not direct Chinese Sports Lottery official API quotations. All timestamps are
source-declared event times, separately from time of collection.
"""
import argparse
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Asia/Shanghai")
ROOT="http://zk.bjjckx.com"
HEAD={"User-Agent":"MFM-odds-data-audit/1.0",
      "Accept":"application/json, text/plain, */*",
      "Referer":ROOT+"/"}
FIELDS=("matchInfo","matchNum","hostTeam","guestTeam","gameTime","matchName")
# Narrow, explicitly reviewed aliases within Caidao; not independent fixture verification.
TEAM_NAME_ALIASES={"珀斯":"珀斯光荣"}
def canonical_team_name(value):
    if not isinstance(value,str):return value
    name=" ".join(value.split())
    return TEAM_NAME_ALIASES.get(name,name)
def get_json(path,params,method="GET"):
    url=ROOT+path
    headers=dict(HEAD)
    body=None
    if method=="GET":
        url+="?"+urllib.parse.urlencode(params)
    else:
        body=urllib.parse.urlencode(params).encode("utf-8")
        headers["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8"
    request=urllib.request.Request(url,data=body,headers=headers,method=method)
    with urllib.request.urlopen(request,timeout=15) as resp:
        data=resp.read(2_000_001)
        if len(data)>2_000_000:raise ValueError("PUBLIC_RESPONSE_EXCEEDS_2MB")
        response=json.loads(data)
    if not isinstance(response,dict):
        raise ValueError("NON_OBJECT_JSON")
    return response

def parse_prices(source):
    if not isinstance(source,str):return None
    values=source.split("|")
    if len(values)!=3:return None
    try:nums=[float(x.strip()) for x in values]
    except ValueError:return None
    if not all(1.0 < x < 1000.0 for x in nums):return None
    return dict(zip(("home","draw","away"),nums))

def parse_timestamp(text):
    if not isinstance(text,str):return None
    try:return dt.datetime.strptime(text,"%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
    except ValueError:return None

def parse_history(payload,fixture,observed_at):
    result=payload.get("result")
    summary={"source_status":payload.get("status"),
             "source_business_message":str(payload.get("message",""))[:100],
             "match_id":fixture["matchInfo"],
             "match_number":fixture.get("matchNum"),
             "fixture_home":fixture.get("hostTeam"),"fixture_away":fixture.get("guestTeam"),
             "source_identity_verified":False,"market":"UNKNOWN",
             "history":[],"invalid_records":0}
    if not isinstance(result,dict):
        summary["reason"]="MISSING_RESULT_OBJECT"
        return summary
    summary["provider_match_number"]=result.get("matchNum")
    summary["provider_home"]=result.get("hostTeam")
    summary["provider_away"]=result.get("guestTeam")
    summary["market"]=result.get("wf")
    summary["integer_handicap"]=result.get("concedeNum")
    summary["source_identity_alias_used"]=any(
        isinstance(provider,str) and isinstance(fixture_name,str)
        and provider!=fixture_name
        and canonical_team_name(provider)==canonical_team_name(fixture_name)
        for provider,fixture_name in ((summary["provider_home"],summary["fixture_home"]),
                                      (summary["provider_away"],summary["fixture_away"])))
    summary["source_identity_verified"]=(
        summary["provider_match_number"]==summary["match_number"]
        and canonical_team_name(summary["provider_home"])==canonical_team_name(summary["fixture_home"])
        and canonical_team_name(summary["provider_away"])==canonical_team_name(summary["fixture_away"]))
    entries=result.get("oddsDetails")
    if not isinstance(entries,list):
        summary["reason"]="NO_HISTORY_LIST"
        return summary
    summary["source_history_count"]=len(entries)
    for entry in entries[:200]:
        if not isinstance(entry,dict):
            summary["invalid_records"]+=1
            continue
        moment=parse_timestamp(entry.get("updateTime"))
        prices=parse_prices(entry.get("odds"))
        if not moment or prices is None or moment>observed_at+dt.timedelta(minutes=5):
            summary["invalid_records"]+=1
            continue
        record={"source_updated_at_bj":moment.isoformat(),
                "source_time_raw":entry.get("updateTime"),
                "home":prices["home"],"draw":prices["draw"],"away":prices["away"],
                "source_odds_flag":entry.get("oddsflag"),
                "provider_num":entry.get("num")}
        summary["history"].append(record)
    summary["history"].sort(key=lambda row:row["source_updated_at_bj"])
    times=[x["source_updated_at_bj"] for x in summary["history"]]
    summary["duplicate_timestamps"]=len(times)-len(set(times))
    summary["history_count"]=len(summary["history"])
    if summary["history"]:
        summary["earliest_source_updated_at_bj"]=times[0]
        summary["latest_source_updated_at_bj"]=times[-1]
    summary["verified_for_model_use"]=(
        summary["source_status"]==200
        and summary["source_identity_verified"]
        and summary["market"]=="spf"
        and len(summary["history"])>0
        and summary["invalid_records"]==0
        and summary["duplicate_timestamps"]==0)
    if not summary["verified_for_model_use"]:
        summary["reason"]="INCOMPLETE_OR_UNVERIFIED_SOURCE_SP_HISTORY"
    return summary

def collect(date,now=None):
    now=now or dt.datetime.now(TZ)
    prefix="F"+date.replace("-","")
    report={"sale_date":date,"retrieved_at_bj":now.isoformat(),
            "provider":"Caidao public H5 backend",
            "provider_category":"THIRD_PARTY_NOT_OFFICIAL_SP",
            "official_sp_verified":False,
            "history_market":"spf",
            "source":"http://zk.bjjckx.com/api/web/game/getJcOddsDetail",
            "forecast_eligibility":"SOURCE_AUDIT_ONLY_NOT_CALIBRATED_PREDICTION",
            "lookahead_warning":"Collection time can be after match kickoff; do not backdate live captures.",
            "fixture_feeds":{},"matches":[],"coverage":{}}
    rows=[]
    for kind in (0,1):
        try:
            response=get_json("/api/web/game/footballQuery",{"type":kind})
            data=response.get("body")
            data=data if isinstance(data,list) else []
            selected=[row for row in data
                      if isinstance(row,dict) and str(row.get("matchInfo","")).startswith(prefix)]
            report["fixture_feeds"][str(kind)]={
                "status":response.get("status"),"all_rows":len(data),"sale_day_rows":len(selected)}
            rows.extend(selected)
        except urllib.error.HTTPError as ex:
            report["fixture_feeds"][str(kind)]={"http_status":ex.code,"error":"HTTPError"}
            if ex.code in (401,403,429,567):
                report["coverage"]["stopped_due_to_access_restriction"]=True
                break
        except (ValueError,OSError) as ex:
            report["fixture_feeds"][str(kind)]={"error_type":type(ex).__name__,"error":str(ex)[:160]}
    unique={}
    for row in rows:
        key=row.get("matchInfo")
        if key and key not in unique:
            unique[key]={k:row.get(k) for k in FIELDS}
    report["coverage"]["fixture_ids"]=len(unique)
    for fid,fixture in sorted(unique.items()):
        record={"fixture":fixture}
        try:
            kickoff=dt.datetime.strptime(str(fixture.get("gameTime")),"%Y%m%d%H%M%S").replace(tzinfo=TZ)
            record["kickoff_bj"]=kickoff.isoformat()
            record["collection_phase"]="AFTER_KICKOFF" if kickoff<=now else "BEFORE_KICKOFF"
        except ValueError:
            record["collection_phase"]="UNKNOWN_KICKOFF"
        try:
            response=get_json("/api/web/game/getJcOddsDetail",{"matchInfo":fid},"POST")
            record["sp_history"]=parse_history(response,fixture,dt.datetime.now(TZ))
            record["pre_kickoff_snapshot_verified"]=(
                record["collection_phase"]=="BEFORE_KICKOFF"
                and record["sp_history"]["verified_for_model_use"])
        except urllib.error.HTTPError as ex:
            record["sp_history"]={"http_status":ex.code,"error":"HTTPError"}
            if ex.code in (401,403,429,567):
                report["coverage"]["stopped_due_to_access_restriction"]=True
                report["matches"].append(record)
                break
        except (OSError,ValueError) as ex:
            record["sp_history"]={"error_type":type(ex).__name__,"error":str(ex)[:180]}
        report["matches"].append(record)
        time.sleep(0.35)
    report["coverage"].update({
        "matches_checked":len(report["matches"]),
        "matches_with_any_history":sum(m.get("sp_history",{}).get("history_count",0)>0 for m in report["matches"]),
        "matches_with_verified_spf_history":sum(m.get("sp_history",{}).get("verified_for_model_use",False) for m in report["matches"]),
        "prematch_snapshots_eligible":sum(m.get("pre_kickoff_snapshot_verified",False) for m in report["matches"]),
        "total_valid_history_rows":sum(m.get("sp_history",{}).get("history_count",0) for m in report["matches"]),
        "before_kickoff_at_collection":sum(m.get("collection_phase")=="BEFORE_KICKOFF" for m in report["matches"]),
        "after_kickoff_at_collection":sum(m.get("collection_phase")=="AFTER_KICKOFF" for m in report["matches"]),
    })
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",default=dt.datetime.now(TZ).date().isoformat())
    args=parser.parse_args()
    dt.date.fromisoformat(args.date)
    report=collect(args.date)
    root=pathlib.Path("mfm-data/caidao-history")/args.date
    root.mkdir(parents=True,exist_ok=True)
    timestamp=dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")
    target=root/(timestamp+".json")
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(target),"coverage":report["coverage"]},ensure_ascii=False))

if __name__=="__main__":
    main()
