#!/usr/bin/env python3
"""OpenFootball public-domain JSON archive ingestion, with as-of cutoff and audit."""
import argparse,datetime as dt,json,pathlib,urllib.request
BASE="https://raw.githubusercontent.com/openfootball/football.json/master"
LEAGUES={"eng.1":"en.1","eng.2":"en.2","ita.1":"it.1","esp.1":"es.1","ger.1":"de.1","fra.1":"fr.1","fra.2":"fr.2"}
def run(day,out):
 cutoff=dt.date.fromisoformat(day);out.mkdir(parents=True,exist_ok=True)
 seasons=[f"{(cutoff.year-1)%100:02d}{cutoff.year%100:02d}",f"{cutoff.year%100:02d}{(cutoff.year+1)%100:02d}"]
 dirs=[f"{cutoff.year-1}-{str(cutoff.year)[-2:]}",f"{cutoff.year}-{str(cutoff.year+1)[-2:]}"]
 audit=[];rows=[]
 for league,code in LEAGUES.items():
  for season in dirs:
   url=f"{BASE}/{season}/{code}.json"
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"MFM-Research/0.3"}),timeout=12) as response:payload=json.load(response)
    count=0
    for m in payload.get("matches",[]):
     date=m.get("date");score=m.get("score",{}).get("ft") if isinstance(m.get("score"),dict) else None
     try:valid=date and dt.date.fromisoformat(date)<cutoff and isinstance(score,list) and len(score)==2 and all(isinstance(v,int) for v in score)
     except ValueError:valid=False
     if not valid:continue
     rows.append({"source":"OpenFootball","league":league,"season":season,"date":date,"home":m.get("team1"),"away":m.get("team2"),"home_goals":score[0],"away_goals":score[1],"source_url":url})
     count+=1
    audit.append({"url":url,"status":"OK","completed_prior":count})
   except Exception as e:audit.append({"url":url,"status":"UNAVAILABLE","reason":str(e)[:120]})
 out.joinpath(f"{day}_openfootball_history.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 summary={"date":day,"matches":len(rows),"successful_sources":sum(x["status"]=="OK" for x in audit),"source_checks":audit,"note":"Public-domain archive, freshness and team-name mapping require separate validation; no bookmaker inputs."}
 out.joinpath(f"{day}_openfootball_audit.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 print(json.dumps({"openfootball_matches":len(rows),"successful_sources":summary["successful_sources"]}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--date",default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat());p.add_argument("--dir",default="mfm_data");a=p.parse_args();run(a.date,pathlib.Path(a.dir))
