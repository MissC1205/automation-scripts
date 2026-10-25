#!/usr/bin/env python3
"""MFM source-quality gate. Audits evidence availability; never emits betting predictions."""
import argparse
import csv
import datetime as dt
import json
import pathlib

def read_json(root, name):
    file = root / name
    if not file.is_file():
        return None
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

def run(date, root):
    stem = date + "_"
    audit = {
        "date": date,
        "collected_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": "Data lineage and prediction eligibility audit, not a prediction",
    }
    file = root / (stem + "matches.csv")
    try:
        with file.open(encoding="utf-8-sig", newline="") as stream:
            espn = list(csv.DictReader(stream))
    except (OSError, ValueError):
        espn = []
    espn_keys = [(x.get("league"), x.get("event_id")) for x in espn]
    unfinished_scores = sum(
        x.get("status") not in {"STATUS_FINAL", "STATUS_FULL_TIME", "STATUS_POSTPONED_FINAL"}
        and x.get("home_score") not in ("", None)
        and x.get("away_score") not in ("", None)
        for x in espn
    )
    audit["espn"] = {
        "fixture_rows": len(espn),
        "unique_fixture_keys": len(set(espn_keys)),
        "duplicate_keys": len(espn_keys) - len(set(espn_keys)),
        "scheduled_rows_with_score_fields": unfinished_scores,
        "warning": "ESPN event IDs are not Chinese JC fixture numbers; may be a small subset of daily events",
    }
    api = read_json(root, stem + "api_football_fixtures.json")
    api_audit = read_json(root, stem + "api_football_audit.json") or {}
    api = api if isinstance(api, list) else []
    ids = [x.get("fixture_id") for x in api if isinstance(x, dict)]
    missing_names = sum(not x.get("home") or not x.get("away") for x in api)
    youth = sum(
        any(tag in ((x.get("home") or "") + " " + (x.get("away") or "") + " " + (x.get("league") or "")).lower()
            for tag in ("u17", "u18", "u19", "u20", "u21", "u23", "youth"))
        for x in api
    )
    audit["api_football"] = {
        "source_status": api_audit.get("status", "MISSING"),
        "fixture_rows": len(api),
        "unique_ids": len(set(ids)),
        "duplicate_or_missing_ids": len(ids) - len(set(ids)) + sum(x is None for x in ids),
        "null_home_or_away": missing_names,
        "youth_fixture_rows_in_unfiltered_feed": youth,
        "distinct_competitions": len({x.get("league_id") for x in api}),
        "warning": "Fixture count is all available competitions/dates, NOT JC coverage or joined current-match sample",
    }
    history = read_json(root, stem + "history_audit.json") or {}
    forms = read_json(root, stem + "team_form.json")
    forms = forms if isinstance(forms, list) else []
    complete = [x for x in forms if x.get("home_form", {}).get("n", 0) >= 5
                and x.get("away_form", {}).get("n", 0) >= 5]
    audit["espn_form"] = {
        "fixture_forms": len(forms),
        "fixtures_with_5_prior_matches_per_team": len(complete),
        "lookback_days": history.get("days_back"),
        "warning": f"Within-league only; {history.get('days_back', 'unknown')} days lookback may still omit cross-competition and postponed matches",
    }
    op = read_json(root, stem + "openfootball_audit.json") or {}
    audit["openfootball"] = {
        "historic_matches_unjoined": op.get("matches", 0),
        "source_files_accessible": op.get("successful_sources", 0),
        "warning": "No team ID crosswalk or as-of feature join is implemented",
    }
    audit["downstream_gates"] = {
        "official_jc_fixture_number_and_sale_state": "NOT_COLLECTED",
        "official_jc_sp_and_integer_handicap": "NOT_COLLECTED",
        "verified_event_time_odds_series": "NOT_COLLECTED",
        "cross_provider_team_id_join": "NOT_IMPLEMENTED",
        "verified_lineups_and_xg": "NOT_COLLECTED",
        "calibrated_1x2_draw_margin_goals": "NOT_IMPLEMENTED",
        "validated_ev_and_best_two_leg": "NOT_IMPLEMENTED",
        "notion_auto_sync_and_official_settlement": "NOT_IMPLEMENTED",
    }
    audit["betting_eligibility"] = "BLOCKED"
    audit["reasons"] = [
        "Missing official JC match/market identity and source-timestamped SP",
        "Missing verified provider-to-JC fixture mapping and full team-form coverage",
        "Missing reproducible calibrated match probabilities and positive-EV selection",
    ]
    root.mkdir(parents=True, exist_ok=True)
    target = root / (stem + "data_quality_gate.json")
    target.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gate": audit["betting_eligibility"],
        "espn_rows": len(espn), "espn_form_5_each": len(complete),
        "api_rows": len(api), "api_status": audit["api_football"]["source_status"],
        "api_youth_rows": youth, "openfootball_unjoined": audit["openfootball"]["historic_matches_unjoined"],
        "audit_file": str(target)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--dir", default="mfm_data")
    args = parser.parse_args()
    dt.date.fromisoformat(args.date)
    raise SystemExit(run(args.date, pathlib.Path(args.dir)))
