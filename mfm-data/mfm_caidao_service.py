#!/usr/bin/env python3
"""MFM Caidao operational collector.

Public, read-only Caidao H5 responses only. A source-stamped research data
pipeline, NOT an official Chinese JC feed or a prediction/EV engine.
No access-control circumvention, credentials, paid predictions, or other-user
information is acquired. All timestamps are Beijing local with offset.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import time
import urllib.error
from zoneinfo import ZoneInfo

import mfm_caidao_daily as detail_api
import mfm_caidao_history as sp_api
import mfm_kelly as kelly_shadow

TZ=ZoneInfo("Asia/Shanghai")
RETRY_ERRORS=(TimeoutError,ConnectionError,urllib.error.URLError)
MAX_MATCHES=100
MARKETS=("spfOdds","rqspfOdds","concedeNum","bfOdds","zjqOdds","bqcOdds")
EXCLUDED={"poissonDistributionStr","matchAnalysis","spfyc","sfyc","zjqyc","bqcyc","dxyc"}
def utc_bj_now():
    return dt.datetime.now(TZ)

def status_ok(payload):
    if not isinstance(payload,dict):
        return False
    return str(payload.get("status"))=="200"

def fetch(path,params,method="GET",retries=2,sleep=time.sleep):
    """Retry only transient network/server errors; respect 401/403/429/567."""
    for attempt in range(retries+1):
        try:
            return sp_api.get_json(path,params,method)
        except urllib.error.HTTPError as exc:
            if exc.code in (401,403,429,567):
                raise
            if exc.code not in (500,502,503,504) or attempt==retries:
                raise
        except RETRY_ERRORS:
            if attempt==retries:
                raise
        sleep(min(2.0,0.6*(attempt+1)))
    raise RuntimeError("UNEXPECTED_RETRY_END")

def match_identity_valid(match_id,sale_date):
    return bool(isinstance(match_id,str)
        and re.fullmatch("F"+sale_date.replace("-","")+r"\d{3,4}",match_id))

def market_prices(fixture):
    out={"raw":{},"spf":None,"integer_handicap":None,"handicap_sp":None,
         "handicap_status":"NOT_VERIFIED","goal_totals":None}
    for k in MARKETS:
        v=fixture.get(k)
        if isinstance(v,(int,float,str)) and len(str(v))<=350:
            out["raw"][k]=v
    out["spf"]=sp_api.parse_prices(fixture.get("spfOdds"))
    try:
        handicap=int(fixture.get("concedeNum"))
        out["integer_handicap"]=handicap
    except (TypeError,ValueError):
        pass
    odds=sp_api.parse_prices(fixture.get("rqspfOdds"))
    if odds and out["integer_handicap"] is not None:
        out["handicap_sp"]=odds
        out["handicap_status"]="THIRD_PARTY_REPORTED_NEEDS_OFFICIAL_CONFIRMATION"
    goals=fixture.get("zjqOdds")
    if isinstance(goals,str):
        try:
            vals=[float(x) for x in goals.split("|")]
            if len(vals)==8 and all(1.0<x<1000.0 for x in vals):
                out["goal_totals"]=vals
        except ValueError:
            pass
    return out

def parse_kickoff(value):
    try:
        return dt.datetime.strptime(str(value),"%Y%m%d%H%M%S").replace(tzinfo=TZ)
    except (TypeError,ValueError):
        return None

def summary_feature(key,value):
    return detail_api.schema_summary(key,value)

def parse_detail(payload,source_time):
    out={"business_status":payload.get("status") if isinstance(payload,dict) else None,
         "retrieved_at_bj":source_time.isoformat(),
         "raw_football_fields":{},
         "third_party_prediction_fields_excluded":sorted(EXCLUDED),
         "feature_coverage":{}}
    data=payload.get("data") if isinstance(payload,dict) else None
    if not status_ok(payload) or not isinstance(data,dict):
        out["status"]="NO_VALID_DETAIL_OBJECT"
        return out
    out["status"]="SOURCE_DETAIL_AVAILABLE"
    out["provider_update_time_raw"]=data.get("updateTime")
    for key in ("historyDataStr","matchFeatureStr","injurySuspensionStr",
                "matchTableStr","matchTableDetailStr"):
        out["feature_coverage"][key]=summary_feature(key,data.get(key))
    out["raw_football_fields"]=detail_api.selected_raw_team_metrics(data.get("matchFeatureStr"))
    out["raw_features_are_provider_reported_not_independently_verified"]=True
    h=out["feature_coverage"].get("historyDataStr",{})
    out["h2h_record_count"]=h.get("history_match_count")
    out["injury_data_presence_only_not_absence_verification"]=bool(
        out["feature_coverage"].get("injurySuspensionStr",{}).get("present"))
    out["independent_model_1x2_probability"]=None
    return out

def identity_signature(row):
    """Provider identity tuple; do not silently merge conflicting match IDs."""
    return tuple(" ".join(str(row.get(key) or "").split()).casefold()
                 for key in ("matchNum","hostTeam","guestTeam","gameTime"))

def select_fixtures(sale_date,transport=fetch):
    """Join active and recent-result pools, validating date-specific IDs."""
    fixtures={}
    sources={}
    restricted=False
    conflicts=[]
    quarantined=set()
    for pool in (0,1):
        try:
            payload=transport("/api/web/game/footballQuery",{"type":pool},"GET")
            body=payload.get("body") if isinstance(payload,dict) else None
            if not status_ok(payload) or not isinstance(body,list):
                sources[str(pool)]={"status":"ERROR_OR_NO_LIST",
                    "provider_status":payload.get("status") if isinstance(payload,dict) else None}
                continue
            picked=[x for x in body if isinstance(x,dict)
                    and match_identity_valid(x.get("matchInfo"),sale_date)]
            sources[str(pool)]={"status":"SUCCESS","raw_rows":len(body),
                                "date_rows":len(picked)}
            for record in picked:
                ident=record["matchInfo"]
                # Conflicting provider records must not be merged or predicted.
                if ident in quarantined:
                    continue
                previous=fixtures.get(ident)
                if previous is not None:
                    if identity_signature(previous)!=identity_signature(record):
                        conflicts.append({"match_id":ident,
                            "first":dict(zip(("number","home","away","kickoff"),identity_signature(previous))),
                            "conflicting":dict(zip(("number","home","away","kickoff"),identity_signature(record))),
                            "source_pool":pool})
                        fixtures.pop(ident,None)
                        quarantined.add(ident)
                    continue
                fixtures[ident]=record
        except urllib.error.HTTPError as exc:
            sources[str(pool)]={"status":"HTTP_ERROR","http_status":exc.code}
            if exc.code in (401,403,429,567):
                restricted=True
                break
        except (ValueError,OSError) as exc:
            sources[str(pool)]={"status":"ERROR","error_type":type(exc).__name__,
                                "message":str(exc)[:140]}
    # The provider date prefix alone does not establish a unique JC number.
    # Two different IDs claiming the same sale-day number are ambiguous:
    # quarantine both rather than silently selecting one for a prediction.
    seen_numbers={}
    for ident,record in list(fixtures.items()):
        number=" ".join(str(record.get("matchNum") or "").split())
        if not number:
            continue
        other=seen_numbers.get(number)
        if other and other!=ident:
            conflicts.append({"match_id":ident,"other_match_id":other,
                              "jc_number":number,
                              "reason":"DUPLICATE_JC_NUMBER_DIFFERENT_IDS"})
            quarantined.update((ident,other))
        else:
            seen_numbers[number]=ident
    for ident in quarantined:
        fixtures.pop(ident,None)
    if conflicts:
        sources["identity_conflicts"]=conflicts
        sources["quarantined_fixture_ids"]=sorted(quarantined)
    return dict(sorted(fixtures.items())[:MAX_MATCHES]),sources,restricted

def spf_history_trend_status(history):
    """A single source quote is a snapshot, never evidence of a price trend."""
    if not history.get("verified_for_model_use"):
        return "UNVERIFIED_OR_MISSING"
    quotes=history.get("history") or []
    if len(quotes)<2:
        return "SINGLE_SNAPSHOT_NO_TREND"
    values={(q.get("home"),q.get("draw"),q.get("away")) for q in quotes}
    return ("MULTI_SNAPSHOT_PRICE_CHANGE" if len(values)>1
            else "MULTI_SNAPSHOT_NO_PRICE_CHANGE")

def evaluate_match(row,sale_date,now,transport=fetch):
    ident=row["matchInfo"]
    kickoff=parse_kickoff(row.get("gameTime"))
    collected_now=utc_bj_now()
    result={
      "match_id":ident,"jc_number":row.get("matchNum"),
      "home":row.get("hostTeam"),"away":row.get("guestTeam"),
      "competition":row.get("matchName"),
      "kickoff_bj":kickoff.isoformat() if kickoff else None,
      "snapshot_captured_at_bj":collected_now.isoformat(),
      "collection_phase":"PRE_KICKOFF" if kickoff and collected_now<kickoff
            else ("POST_KICKOFF" if kickoff else "UNKNOWN"),
      "source_market":market_prices(row),
      "detail":{},"spf_history":{},"data_quality":{}
    }
    if not (isinstance(result["home"],str) and result["home"]
            and isinstance(result["away"],str) and result["away"]
            and isinstance(result["jc_number"],str)):
        result["data_quality"]["identity"]="MISSING_FIXTURE_LABELS"
    else:
        result["data_quality"]["identity"]="DATE_BOUND_ID_WITH_PROVIDER_TEAMS"
    try:
        data=transport("/api/web/game/getMatchAllData",{"matchInfo":ident},"POST")
        result["detail"]=parse_detail(data,utc_bj_now())
    except urllib.error.HTTPError as exc:
        result["detail"]={"status":"HTTP_ERROR","http_status":exc.code}
        if exc.code in (401,403,429,567):
            result["stop_on_restricted_access"]=True
            return result
    except (ValueError,OSError) as exc:
        result["detail"]={"status":"ERROR","error_type":type(exc).__name__,
                          "message":str(exc)[:140]}
    try:
        response=transport("/api/web/game/getJcOddsDetail",{"matchInfo":ident},"POST")
        fixture={k:row.get(k) for k in ("matchInfo","matchNum","hostTeam","guestTeam")}
        result["spf_history"]=sp_api.parse_history(response,fixture,utc_bj_now())
    except urllib.error.HTTPError as exc:
        result["spf_history"]={"status":"HTTP_ERROR","http_status":exc.code}
        if exc.code in (401,403,429,567):
            result["stop_on_restricted_access"]=True
            return result
    except (ValueError,OSError) as exc:
        result["spf_history"]={"status":"ERROR","error_type":type(exc).__name__,
                               "message":str(exc)[:140]}
    hist=result.get("spf_history",{})
    approved=bool(hist.get("verified_for_model_use"))
    result["data_quality"]["history_spf_valid"]=approved
    result["data_quality"]["history_spf_quote_count"]=hist.get("history_count",0)
    result["data_quality"]["spf_history_trend_status"]=spf_history_trend_status(hist)
    result["data_quality"]["history_as_of"]=hist.get("latest_source_updated_at_bj")
    result["data_quality"]["true_prematch_snapshot"]=(
        result["collection_phase"]=="PRE_KICKOFF" and approved)
    current=result["source_market"]["spf"]
    latest=hist.get("history",[])[-1] if hist.get("history") else None
    if current and isinstance(latest,dict):
        is_same=all(abs(current[k]-latest[k])<=0.011 for k in ("home","draw","away"))
        result["data_quality"]["current_sp_vs_latest_history"]="MATCH" if is_same else "DIFFERENT_SNAPSHOT_OR_PROVIDER_LAG"
    else:
        result["data_quality"]["current_sp_vs_latest_history"]="UNTESTED"
    result["data_quality"]["market_officially_verified"]=False
    result["data_quality"]["probability_model_calibrated"]=False
    # Never allow vendor model probability as evidence for independent output.
    result["model_features"]={
        "usable_as_third_party_research_inputs":result["detail"].get("raw_football_fields",{}),
        "prematch_independent_feature_validation":"NOT_COMPLETED",
        "vendor_prediction_outputs_excluded":True,
        "independent_1x2_prediction":None,
        "independent_handicap_prediction":None,
        "calibrated_ev":None
    }
    return result

def collect(sale_date,now=None,transport=fetch,pause=time.sleep):
    now=now or utc_bj_now()
    dt.date.fromisoformat(sale_date)
    fixtures,sources,restricted=select_fixtures(sale_date,transport)
    report={
        "format_version":"1.0","sale_date_bj":sale_date,
        "collection_started_at_bj":now.isoformat(),
        "source_provider":"Caidao 采道 public H5",
        "source_type":"THIRD_PARTY_AGGREGATOR_NOT_OFFICIAL_JC",
        "source_url":"http://zk.bjjckx.com",
        "access_scope":"UNAUTHENTICATED_PUBLIC_READ_ONLY",
        "sp_prices_are_officially_verified":False,
        "provider_predictions_used_in_model":False,
        "date_identity_mapping":"MATCH_ID_PREFIX_VALIDATED_MATCH_NAME_PROVIDER_REPORTED",
        "fixture_identity_independently_verified":False,
        "fixture_identity_conflicts":sources.get("identity_conflicts",[]),
        "independent_model_status":"NOT_IMPLEMENTED_OR_NOT_CALIBRATED",
        "final_prediction_status":"NOT_GENERATED_BY_COLLECTOR",
        "fixture_sources":sources,
        "matches":[],
        "coverage":{},
        "quality_gate":"NO_DATA"
    }
    report["coverage"]["fixture_ids"]=len(fixtures)
    if restricted:
        report["access_restriction_encountered"]=True
    # Both source pools are necessary to recover the full sale-day slate:
    # type=0 has upcoming games and type=1 has already-started/finished games.
    # Never report full research coverage when one pool silently failed.
    report["fixture_pool_integrity"]="COMPLETE" if all(
        sources.get(str(pool),{}).get("status")=="SUCCESS" for pool in (0,1)
    ) and not report["fixture_identity_conflicts"] else "PARTIAL_SOURCE_POOL"
    for fid,fixture in fixtures.items():
        record=evaluate_match(fixture,sale_date,now,transport)
        report["matches"].append(record)
        if record.get("stop_on_restricted_access"):
            report["access_restriction_encountered"]=True
            break
        pause(0.25)
    rows=report["matches"]
    report["collection_finished_at_bj"]=utc_bj_now().isoformat()
    report["coverage"].update({
      "matches_evaluated":len(rows),
      "current_spf_prices":sum(m["source_market"]["spf"] is not None for m in rows),
      "current_handicap_prices":sum(m["source_market"]["handicap_sp"] is not None for m in rows),
      "reported_handicap_numbers":sum(m["source_market"]["integer_handicap"] is not None for m in rows),
      "detail_objects":sum(m["detail"].get("status")=="SOURCE_DETAIL_AVAILABLE" for m in rows),
      "historical_spf_matches_verified":sum(m["spf_history"].get("verified_for_model_use",False) for m in rows),
      "historical_spf_rows":sum(m["spf_history"].get("history_count",0) for m in rows),
      "historical_spf_single_snapshot_matches":sum(m["data_quality"].get("spf_history_trend_status")=="SINGLE_SNAPSHOT_NO_TREND" for m in rows),
      "historical_spf_multi_snapshot_matches":sum(m["data_quality"].get("spf_history_trend_status") in ("MULTI_SNAPSHOT_NO_PRICE_CHANGE","MULTI_SNAPSHOT_PRICE_CHANGE") for m in rows),
      "historical_spf_price_change_matches":sum(m["data_quality"].get("spf_history_trend_status")=="MULTI_SNAPSHOT_PRICE_CHANGE" for m in rows),
      "current_spf_matches_latest_history":sum(m["data_quality"].get("current_sp_vs_latest_history")=="MATCH" for m in rows),
      "current_spf_divergence_or_lag":sum(m["data_quality"].get("current_sp_vs_latest_history")=="DIFFERENT_SNAPSHOT_OR_PROVIDER_LAG" for m in rows),
      "captured_before_kickoff":sum(m["collection_phase"]=="PRE_KICKOFF" for m in rows),
      "captured_after_kickoff":sum(m["collection_phase"]=="POST_KICKOFF" for m in rows),
      "prematch_verified_history_snapshots":sum(m["data_quality"].get("true_prematch_snapshot",False) for m in rows),
      "third_party_handicap_historical_rows":0,
      "verified_official_jc_sp_matches":0
    })
    n=len(rows)
    count=report["coverage"]
    if not n:
        report["quality_gate"]="NO_DATA"
    elif (not report.get("access_restriction_encountered") and
          report["fixture_pool_integrity"]=="COMPLETE" and
          n==len(fixtures) and count["current_spf_prices"]==n and
          count["detail_objects"]==n and count["historical_spf_matches_verified"]==n and
          all(m["data_quality"].get("identity")=="DATE_BOUND_ID_WITH_PROVIDER_TEAMS"
              and m["kickoff_bj"] is not None for m in rows)):
        report["quality_gate"]="RESEARCH_DATA_AVAILABLE"
    else:
        report["quality_gate"]="PARTIAL_RESEARCH_DATA"
    report["odds_trend_gate"]=("NO_MULTI_SNAPSHOT_TREND" if count["historical_spf_multi_snapshot_matches"]==0
        else ("PARTIAL_MULTI_SNAPSHOT_COVERAGE" if count["historical_spf_multi_snapshot_matches"]<n
              else "MULTI_SNAPSHOT_COVERAGE_NOT_OFFICIAL"))
    report["betting_gate"]="BLOCKED_REQUIRES_OFFICIAL_SP_INDEPENDENT_PROBABILITIES_AND_EV"
    report["known_gaps"]=[
       "Caidao third-party quotes have not been directly matched to official JC feed",
       "Fixture team identities and kickoffs are not independently verified against primary schedules",
       "No verified time-series for official integer-handicap H-HAD odds",
       "A single SPF quote does not prove historical odds movement; check odds_trend_gate and price-change coverage",
       "Provider form/lineups/injuries not individually verified against original team/league sources",
       "No calibrated evidence-only 1X2/draw/score/handicap model run",
       "Provider probabilities and prose excluded to preserve independent model firewall",
       "GitHub schedule timestamps and provider update timestamps are not guaranteed simultaneous"
    ]
    return report

def persist(report,out_root):
    sale=report["sale_date_bj"]
    root=pathlib.Path(out_root)
    target=root/sale
    target.mkdir(parents=True,exist_ok=True)
    stamp=utc_bj_now().strftime("%Y%m%dT%H%M%S%f%z")
    raw=json.dumps(report,ensure_ascii=False,indent=2)
    archive=target/(stamp+".json")
    archive.write_text(raw,encoding="utf-8")
    (target/"latest.json").write_text(raw,encoding="utf-8")
    # A historical date refresh must never clobber the today's global shortcut.
    is_current_sale_day=(sale==utc_bj_now().date().isoformat())
    if is_current_sale_day:
        (root/"latest.json").write_text(raw,encoding="utf-8")
    # Hard separation: evidence-only football features are exported without odds.
    # The independent prediction stage must freeze its result before reading
    # the market-only view. This collector itself never produces a forecast.
    football_only={
        "sale_date_bj":sale,
        "source":"Caidao third-party reported football form; independent validation incomplete",
        "created_at_bj":report["collection_finished_at_bj"],
        "contains_odds_or_vendor_probabilities":False,
        "calibrated_prediction_generated":False,
        "matches":[{
            "match_id":m["match_id"],"jc_number":m["jc_number"],
            "home":m["home"],"away":m["away"],
            "kickoff_bj":m["kickoff_bj"],
            "collection_phase":m["collection_phase"],
            "form_data":m["model_features"].get("usable_as_third_party_research_inputs",{}),
            "historical_head_to_head_count":m["detail"].get("h2h_record_count"),
            "injury_information_present_unverified":m["detail"].get("injury_data_presence_only_not_absence_verification",False),
            "missing_primary_source_verification":True
        } for m in report["matches"]]
    }
    market_only={
        "sale_date_bj":sale,"collected_at_bj":report["collection_finished_at_bj"],
        "source":"Caidao THIRD_PARTY_NOT_OFFICIAL",
        "to_be_read_after_freezing_independent_forecast":True,
        "matches":[{
            "match_id":m["match_id"],"jc_number":m["jc_number"],
            "collection_phase":m["collection_phase"],
            "market":m["source_market"],
            "spf_history":m["spf_history"],
            "sp_current_vs_history":m["data_quality"].get("current_sp_vs_latest_history")
        } for m in report["matches"]]
    }
    (target/"football-only.json").write_text(json.dumps(football_only,ensure_ascii=False,indent=2),encoding="utf-8")
    if is_current_sale_day:
        (root/"latest-football-only.json").write_text(json.dumps(football_only,ensure_ascii=False,indent=2),encoding="utf-8")
    (target/"market-only.json").write_text(json.dumps(market_only,ensure_ascii=False,indent=2),encoding="utf-8")
    # Shadow-only Kelly diagnostics from already separated market data.
    # Caidao currently lacks verified multi-bookmaker identities, independent
    # calibrated probabilities, and official SP. Keep stake outputs BLOCKED.
    kelly_report=kelly_shadow.market_snapshot_shadow(market_only)
    (target/"kelly-shadow.json").write_text(json.dumps(
        kelly_report,ensure_ascii=False,indent=2),encoding="utf-8")
    if is_current_sale_day:
        (root/"latest-kelly-shadow.json").write_text(json.dumps(
            kelly_report,ensure_ascii=False,indent=2),encoding="utf-8")
    if is_current_sale_day:
        (root/"latest-market-only.json").write_text(json.dumps(market_only,ensure_ascii=False,indent=2),encoding="utf-8")
    digest={
        "date":sale,"collected_at_bj":report["collection_finished_at_bj"],
        "last_snapshot_path":str(archive),
        "quality_gate":report["quality_gate"],
        "odds_trend_gate":report["odds_trend_gate"],
        "fixture_pool_integrity":report["fixture_pool_integrity"],
        "fixture_identity_conflicts":report["fixture_identity_conflicts"],
        "fixture_identity_independently_verified":False,
        "fixture_sources":report["fixture_sources"],
        "betting_gate":report["betting_gate"],
        "coverage":report["coverage"],
        "match_summary":[{
           "id":m["match_id"],"number":m["jc_number"],"home":m["home"],"away":m["away"],
           "kickoff_bj":m["kickoff_bj"],"collection_phase":m["collection_phase"],
           "spf":m["source_market"]["spf"],
           "hhad_line":m["source_market"]["integer_handicap"],
           "hhad_sp":m["source_market"]["handicap_sp"],
           "spf_history_rows":m["spf_history"].get("history_count",0),
           "spf_history_trend_status":m["data_quality"].get("spf_history_trend_status"),
           "last_source_sp_updated_at_bj":m["spf_history"].get("latest_source_updated_at_bj"),
           "prematch_snapshot_verified":m["data_quality"].get("true_prematch_snapshot",False),
           "detail_available":m["detail"].get("status")=="SOURCE_DETAIL_AVAILABLE"
        } for m in report["matches"]]
    }
    text=json.dumps(digest,ensure_ascii=False,indent=2)
    (target/"summary.json").write_text(text,encoding="utf-8")
    if is_current_sale_day:
        (root/"latest-summary.json").write_text(text,encoding="utf-8")
    (root/"last-run.json").write_text(json.dumps({
        "requested_sale_date":sale,
        "collected_at_bj":report["collection_finished_at_bj"],
        "quality_gate":report["quality_gate"],
        "coverage":report["coverage"],
        "archive":str(archive)
    },ensure_ascii=False,indent=2),encoding="utf-8")
    return archive

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",default=os.environ.get("SALE_DATE") or utc_bj_now().date().isoformat())
    parser.add_argument("--out",default="mfm-data/caidao-live")
    args=parser.parse_args()
    dt.date.fromisoformat(args.date)
    report=collect(args.date)
    target=persist(report,args.out)
    print(json.dumps({"output":str(target),"quality_gate":report["quality_gate"],
                      "coverage":report["coverage"]},ensure_ascii=False))
if __name__=="__main__":
    main()
