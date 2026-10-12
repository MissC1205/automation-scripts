#!/usr/bin/env python3
"""Football-only evidence collector using API-Football team IDs; no betting odds."""
import argparse,datetime as dt,json,os,pathlib,urllib.parse,urllib.request,sys
BASE="https://v3.football.api-sports.io"
FINISHED={"FT","AET","PEN"}
def get(path,params,key):
 url=BASE+path+"?"+urllib.parse.urlencode(params)
 with urllib.request.urlopen(urllib.request.Request(url,headers={"x-apisports-key":key}),timeout=25) as r:obj=json.load(r)
 if obj.get("errors"):raise ValueError(str(obj["errors"])[:180])
 return obj.get("response",[])
def main():
 p=argparse.ArgumentParser();p.add_argument("--date",default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat());p.add_argument("--dir",default="mfm_data");p.add_argument("--max-teams",type=int,default=20);a=p.parse_args()
 out=pathlib.Path(a.dir);file=out/f"{a.date}_api_football_fixtures.json";key=os.getenv("API_FOOTBALL_KEY","")
 if not key or not file.exists():
  print("team evidence: no secret or fixture file; skipped");return 0
 fixtures=json.loads(file.read_text())
 # Prefer near-future events, rather than exhausting quota on unrelated past games.
 target=dt.date.fromisoformat(a.date)
 upcoming=[x for x in fixtures if x.get("status") in ("NS","TBD") and x.get("home_id") and x.get("away_id") and x.get("kickoff","")[:10] in (str(target),str(target+dt.timedelta(days=1)))]
 unique={}
 for x in upcoming:
  for side in ("home","away"):
   ident=x[side+"_id"]
   if ident not in unique:unique[ident]={"id":ident,"name":x[side],"league":x["league"],"season":x["season"]}
 selected=list(unique.values())[:a.max_teams]
 results=[];errors=[]
 for t in selected:
  try:
   raw=get("/fixtures",{"team":t["id"],"last":10},key)
   completed=[]
   for ev in raw:
    f=ev.get("fixture",{});teams=ev.get("teams",{});goals=ev.get("goals",{})
    if f.get("status",{}).get("short") not in FINISHED or not f.get("date","")[:10]<a.date:continue
    if goals.get("home") is None or goals.get("away") is None:continue
    completed.append({"id":f.get("id"),"date":f.get("date"),"home":teams.get("home",{}).get("name"),"away":teams.get("away",{}).get("name"),"home_id":teams.get("home",{}).get("id"),"away_id":teams.get("away",{}).get("id"),"home_goals":goals["home"],"away_goals":goals["away"],"competition":ev.get("league",{}).get("name")})
   completed=completed[:10]
   home=[m for m in completed if m["home_id"]==t["id"]];away=[m for m in completed if m["away_id"]==t["id"]]
   def summary(matches):
    return {"games":len(matches),"gf":sum(m["home_goals"] if m["home_id"]==t["id"] else m["away_goals"] for m in matches),"ga":sum(m["away_goals"] if m["home_id"]==t["id"] else m["home_goals"] for m in matches)}
   results.append({**t,"recent":summary(completed),"at_home":summary(home),"away":summary(away),"matches":completed,"data_status":"PARTIAL" if len(completed)<5 else "RECENT_RESULTS_AVAILABLE"})
  except Exception as e:errors.append({"team_id":t["id"],"error":str(e)})
 out.joinpath(f"{a.date}_api_team_evidence.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
 audit={"date":a.date,"available_fixtures":len(upcoming),"unique_teams":len(unique),"requested_teams":len(selected),"teams_succeeded":len(results),"teams_failed":len(errors),"teams_with_5":sum(x["recent"]["games"]>=5 for x in results),"errors":errors,"note":"Last-10 fixtures may include other competitions. No xG, injuries, or model probability inferred."}
 out.joinpath(f"{a.date}_api_team_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print(json.dumps(audit));return 1 if errors else 0
if __name__=="__main__":sys.exit(main())
