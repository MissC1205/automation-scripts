#!/usr/bin/env python3
"""API-Football authenticated probe. No key or personal data is written to artifacts."""
import argparse,datetime as dt,json,os,pathlib,urllib.request,urllib.parse,sys
BASE="https://v3.football.api-sports.io"
def call(path,key,params=None):
 url=BASE+path+("?" + urllib.parse.urlencode(params) if params else "")
 req=urllib.request.Request(url,headers={"x-apisports-key":key})
 with urllib.request.urlopen(req,timeout=25) as resp:
  payload=json.load(resp)
 if payload.get("errors"):raise RuntimeError("API returned errors: "+str(payload["errors"])[:250])
 return payload
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",default="mfm_data");p.add_argument("--date",default=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d"));a=p.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 key=os.getenv("API_FOOTBALL_KEY","").strip()
 audit={"source":"API-Football","date":a.date,"collected_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"authenticated":False,"requests":[],"note":"This feed does not establish Chinese JC identifiers, official SP or guaranteed xG coverage."}
 if not key:
  audit["status"]="NOT_CONFIGURED"
  (out/f"{a.date}_api_football_audit.json").write_text(json.dumps(audit,indent=2))
  print("API-Football: GitHub secret API_FOOTBALL_KEY not configured; skipped safely")
  return 0
 try:
  status=call("/status",key)
  audit["authenticated"]=True
  audit["requests"].append({"endpoint":"/status","ok":True,"results":status.get("results")})
  # API dates are UTC; request two adjacent dates for Asia/Shanghai football day.
  fixtures=[]
  for date in (a.date,(dt.date.fromisoformat(a.date)+dt.timedelta(days=1)).isoformat()):
   data=call("/fixtures",key,{"date":date,"timezone":"Asia/Shanghai"})
   audit["requests"].append({"endpoint":"/fixtures","date":date,"results":data.get("results"),"ok":True})
   fixtures.extend(data.get("response",[]))
  # Do not leak authentication or copy all provider data to a public repository.
  normalized=[]
  seen=set()
  for x in fixtures:
   fixture=x.get("fixture",{});teams=x.get("teams",{});league=x.get("league",{})
   ident=fixture.get("id")
   if ident in seen:continue
   seen.add(ident)
   normalized.append({"fixture_id":ident,"kickoff":fixture.get("date"),"league_id":league.get("id"),"league":league.get("name"),"season":league.get("season"),"home_id":teams.get("home",{}).get("id"),"home":teams.get("home",{}).get("name"),"away_id":teams.get("away",{}).get("id"),"away":teams.get("away",{}).get("name"),"status":fixture.get("status",{}).get("short")})
  (out/f"{a.date}_api_football_fixtures.json").write_text(json.dumps(normalized,ensure_ascii=False,indent=2))
  audit["status"]="SUCCESS";audit["fixtures"]=len(normalized)
 except Exception as e:
  audit["status"]="FAILED";audit["error"]=str(e)[:300]
 (out/f"{a.date}_api_football_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print(json.dumps({"api_football_status":audit["status"],"authenticated":audit["authenticated"],"fixtures":audit.get("fixtures"),"error":audit.get("error")}))
 return 1 if audit["status"]=="FAILED" else 0
if __name__=="__main__":sys.exit(main())
