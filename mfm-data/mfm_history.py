#!/usr/bin/env python3
"""Evidence-first ESPN historical results for today's fixtures. No bookmaker input."""
import argparse,csv,datetime as dt,json,pathlib,time,urllib.request,urllib.parse
BASE="https://site.api.espn.com/apis/site/v2/sports/soccer"
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"MFM-Research/0.2","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=18) as r:return json.load(r)
def run(day,out,days):
 out.mkdir(parents=True,exist_ok=True)
 fixtures=list(csv.DictReader((out/f"{day}_matches.csv").open(encoding="utf-8-sig")))
 leagues=sorted({r["league"] for r in fixtures})
 cutoff=dt.date.fromisoformat(day)
 history=[];errors=[];calls=0
 for league in leagues:
  for offset in range(1,days+1):
   d=cutoff-dt.timedelta(days=offset)
   url=f"{BASE}/{urllib.parse.quote(league)}/scoreboard?dates={d:%Y%m%d}"
   try:
    data=get(url);calls+=1
    for ev in data.get("events",[]):
     if not ev.get("status",{}).get("type",{}).get("completed"):continue
     c=(ev.get("competitions") or [{}])[0]
     teams=c.get("competitors",[])
     h=next((t for t in teams if t.get("homeAway")=="home"),{})
     a=next((t for t in teams if t.get("homeAway")=="away"),{})
     try:hs=int(h.get("score"));as_=int(a.get("score"))
     except (TypeError,ValueError):continue
     history.append({"league":league,"event_id":ev.get("id"),"date":ev.get("date"),"home":h.get("team",{}).get("displayName"),"away":a.get("team",{}).get("displayName"),"home_score":hs,"away_score":as_,"source_url":url})
   except Exception as e:errors.append({"league":league,"date":str(d),"error":str(e)})
   time.sleep(.08)
 fields=["league","event_id","date","home","away","home_score","away_score","source_url"]
 with (out/f"{day}_history.csv").open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(history)
 teamrows=[]
 for match in fixtures:
  h=match["home"];a=match["away"];league=match["league"]
  def form(team):
   matches=sorted([x for x in history if x["league"]==league and team in (x["home"],x["away"])],key=lambda x:x["date"],reverse=True)[:10]
   gf=sum(x["home_score"] if x["home"]==team else x["away_score"] for x in matches)
   ga=sum(x["away_score"] if x["home"]==team else x["home_score"] for x in matches)
   pts=sum(3 if (x["home_score"]-x["away_score"])*(1 if x["home"]==team else -1)>0 else 1 if x["home_score"]==x["away_score"] else 0 for x in matches)
   return {"n":len(matches),"gf":gf,"ga":ga,"points":pts,"event_ids":[x["event_id"] for x in matches]}
  teamrows.append({"league":league,"fixture_id":match["event_id"],"home":h,"away":a,"home_form":form(h),"away_form":form(a),"coverage":"PARTIAL" if min(form(h)["n"],form(a)["n"])<5 else "AT_LEAST_5","note":"Prior completed league matches only; no xG, injuries or official JC SP"})
 (out/f"{day}_team_form.json").write_text(json.dumps(teamrows,ensure_ascii=False,indent=2),encoding="utf-8")
 audit={"date":day,"days_back":days,"leagues":leagues,"requests_succeeded":calls,"errors":errors,"completed_matches":len(history),"fixtures":len(fixtures),"fixtures_with_5_each":sum(x["coverage"]=="AT_LEAST_5" for x in teamrows),"warning":"Coverage may be low early season. Never treat partial form as a validated forecast."}
 (out/f"{day}_history_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps(audit));return 1 if errors else 0
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--date",default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat());p.add_argument("--dir",default="mfm_data");p.add_argument("--days",type=int,default=21);a=p.parse_args();raise SystemExit(run(a.date,pathlib.Path(a.dir),a.days))
