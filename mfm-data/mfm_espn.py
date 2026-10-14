#!/usr/bin/env python3
"""Fetch ESPN public soccer scoreboards; source data is NOT Chinese lottery SP."""
import argparse,csv,datetime as dt,json,pathlib,sys,urllib.request,urllib.parse
BASE="https://site.api.espn.com/apis/site/v2/sports/soccer"
FIELDS=["source","league","event_id","kickoff_utc","home","away","home_score","away_score","status","collected_at_utc","source_url","data_status"]
def collect(day,leagues,out):
 out.mkdir(parents=True,exist_ok=True);stamp=dt.datetime.now(dt.timezone.utc).isoformat();rows=[];errors=[]
 for league in leagues:
  url=f"{BASE}/{urllib.parse.quote(league)}/scoreboard?dates={day.replace('-','')}"
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"MFM-Research/0.1","Accept":"application/json"})
   with urllib.request.urlopen(req,timeout=20) as response:data=json.load(response)
   (out/f"{day}_{league}_raw.json").write_text(json.dumps({"source_url":url,"collected_at_utc":stamp,"payload":data},ensure_ascii=False,indent=2),encoding="utf-8")
   for ev in data.get("events",[]):
    competition=(ev.get("competitions") or [{}])[0];teams=competition.get("competitors",[])
    home=next((x for x in teams if x.get("homeAway")=="home"),{})
    away=next((x for x in teams if x.get("homeAway")=="away"),{})
    finished=bool(ev.get("status",{}).get("type",{}).get("completed"))
    rows.append(dict(source="ESPN",league=league,event_id=ev.get("id"),kickoff_utc=ev.get("date"),home=home.get("team",{}).get("displayName"),away=away.get("team",{}).get("displayName"),home_score=home.get("score") if finished else None,away_score=away.get("score") if finished else None,status=ev.get("status",{}).get("type",{}).get("name"),collected_at_utc=stamp,source_url=url,data_status="UNVERIFIED_EXTERNAL"))
  except Exception as e:errors.append({"league":league,"error":str(e)})
 with (out/f"{day}_matches.csv").open("w",newline="",encoding="utf-8-sig") as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
 (out/f"{day}_audit.json").write_text(json.dumps({"date":day,"collected_at_utc":stamp,"rows":len(rows),"failures":errors,"note":"ESPN event IDs are NOT JC lottery numbers. No official SP, xG, or verified results."},ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({"date":day,"rows":len(rows),"failures":errors}));return 1 if errors else 0
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--date",default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat());p.add_argument("--leagues",default="eng.1,ita.1,esp.1,ger.1,fra.1");p.add_argument("--out",default="./mfm_data");a=p.parse_args();dt.date.fromisoformat(a.date);sys.exit(collect(a.date,[x.strip() for x in a.leagues.split(",") if x.strip()],pathlib.Path(a.out)))
