#!/usr/bin/env python3
"""MFM enrichment probe: ESPN standings and match summaries, provenance first."""
import argparse,csv,datetime as dt,json,pathlib,time,urllib.request,urllib.parse
BASE="https://site.api.espn.com/apis"
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"MFM-Research/0.2","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=18) as response:return json.load(response)
def main():
 p=argparse.ArgumentParser();p.add_argument("--date",required=True);p.add_argument("--dir",default="mfm_data");p.add_argument("--max-summaries",type=int,default=20);a=p.parse_args()
 root=pathlib.Path(a.dir);rows=list(csv.DictReader((root/f"{a.date}_matches.csv").open(encoding="utf-8-sig")))
 stamp=dt.datetime.now(dt.timezone.utc).isoformat();leagues=sorted(set(x["league"] for x in rows));results=[];failures=[]
 for league in leagues:
  url=f"{BASE}/v2/sports/soccer/{urllib.parse.quote(league)}/standings"
  try:
   payload=fetch(url);(root/f"{a.date}_{league}_standings.json").write_text(json.dumps({"url":url,"collected_at_utc":stamp,"payload":payload},ensure_ascii=False),encoding="utf-8")
   results.append({"type":"standings","league":league,"status":"ok","url":url})
  except Exception as e:failures.append({"type":"standings","league":league,"error":str(e)})
  time.sleep(.15)
 for row in rows[:a.max_summaries]:
  league,event=row["league"],row["event_id"];url=f"{BASE}/site/v2/sports/soccer/{urllib.parse.quote(league)}/summary?event={urllib.parse.quote(event)}"
  try:
   payload=fetch(url);(root/f"{a.date}_{league}_{event}_summary.json").write_text(json.dumps({"url":url,"collected_at_utc":stamp,"payload":payload},ensure_ascii=False),encoding="utf-8")
   results.append({"type":"summary","league":league,"event_id":event,"status":"ok","url":url})
  except Exception as e:failures.append({"type":"summary","league":league,"event_id":event,"error":str(e)})
  time.sleep(.15)
 audit={"date":a.date,"collected_at_utc":stamp,"attempted":len(leagues)+min(len(rows),a.max_summaries),"succeeded":len(results),"failures":failures,"results":results,"warning":"No official JC SP, verified injury status, xG or time-series odds; no betting picks."}
 (root/f"{a.date}_enrichment_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({"enrichment_attempted":audit["attempted"],"enrichment_succeeded":len(results),"enrichment_failures":len(failures),"errors":failures[:8]}))
if __name__=="__main__":main()
