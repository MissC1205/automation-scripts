#!/usr/bin/env python3
"""MFM hourly research handoff. No invented predictions or stale-data promotion."""
import datetime as dt
import json
import pathlib
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
ROOT = pathlib.Path("mfm-data")
SOURCE = ROOT / "caidao-live" / "latest-summary.json"
OUT = ROOT / "analysis-queue"

def main():
    now = dt.datetime.now(TZ)
    OUT.mkdir(parents=True, exist_ok=True)
    if SOURCE.exists():
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
    else:
        data = {}
    source_time = data.get("collected_at_bj")
    try:
        age_h = round((now - dt.datetime.fromisoformat(source_time)).total_seconds()/3600, 2)
    except (TypeError, ValueError):
        age_h = None
    sale_day = now.date().isoformat()
    same_day = data.get("date") == sale_day
    matches = []
    for row in data.get("match_summary", []):
        odds_time = row.get("last_source_sp_updated_at_bj")
        try:
            odds_age = round((now-dt.datetime.fromisoformat(odds_time)).total_seconds()/3600,2)
        except (TypeError, ValueError):
            odds_age = None
        matches.append({
            "id":row.get("id"),"number":row.get("number"),
            "home":row.get("home"),"away":row.get("away"),
            "kickoff_bj":row.get("kickoff_bj"),
            "source_spf":row.get("spf"),"source_handicap":row.get("hhad_line"),
            "source_handicap_sp":row.get("hhad_sp"),
            "source_odds_time":odds_time,"source_odds_age_hours":odds_age,
            "source_odds_stale":odds_age is None or odds_age>3,
            "odds_history_rows":row.get("spf_history_rows",0),
            "research_status":"NEEDS_INDEPENDENT_TEAM_AND_FIXTURE_VERIFICATION",
            "independent_probability":None,"predictions":None,
            "required_evidence":["recent_form","home_away","lineups_injuries",
              "motivation_schedule","multi_source_market_history"],
            "missing_evidence":["official_jc_sp","independent_probability",
              "independent_fixture_verification"],
        })
    warnings=[]
    if not same_day: warnings.append("SNAPSHOT_WRONG_SALE_DATE")
    if age_h is None or age_h>2: warnings.append("SNAPSHOT_STALE")
    if not matches: warnings.append("NO_MATCHES")
    if data.get("coverage",{}).get("verified_official_jc_sp_matches",0)==0:
        warnings.append("OFFICIAL_SP_UNAVAILABLE")
    if not data.get("fixture_identity_independently_verified"):
        warnings.append("FIXTURE_IDENTITY_NOT_INDEPENDENTLY_VERIFIED")
    if any(m["source_odds_stale"] for m in matches):
        warnings.append("SOURCE_ODDS_STALE")
    report={
        "generated_at_bj":now.isoformat(),"sale_date":sale_day,
        "source_snapshot_at_bj":source_time,"source_age_hours":age_h,
        "source_fixture_count":len(matches),"full_jc_pool_verified":False,
        "coverage_status":"UNVERIFIED_DO_NOT_CLAIM_COMPLETE",
        "warnings":warnings,"matches_to_analyze":matches,
        "workflow_rule":"External cross-check and independent modelling required; this handoff is not a prediction.",
        "best_parlay":None,"parlay_reason":"No independently validated probabilities and official prices",
    }
    target=OUT / (now.strftime("%Y%m%dT%H%M%S%z")+".json")
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/"latest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"path":str(target),"matches":len(matches),"warnings":warnings},ensure_ascii=False))
    if "NO_MATCHES" in warnings: raise SystemExit(2)

if __name__=="__main__": main()
