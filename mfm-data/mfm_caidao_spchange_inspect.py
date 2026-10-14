#!/usr/bin/env python3
"""Inspect source-side matchInfoCode construction in Caidao public odds-page JS."""
import datetime as dt,json,pathlib,re,urllib.request
from zoneinfo import ZoneInfo
TZ=ZoneInfo("Asia/Shanghai")
ROOT="http://zk.bjjckx.com"
NAME="package-analysis-game-stake-calc-game-stake-spChange-game-stake-spChange"
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"MFM-public-frontend-audit/1.0"})
    with urllib.request.urlopen(req,timeout=12) as r:return r.read(900000).decode("utf-8",errors="replace")
def main():
    index=get(ROOT+"/static/js/index.e98df7de.js")
    m=re.search(re.escape('"'+NAME+'":"')+r'([0-9a-f]{8})"',index)
    if not m:raise ValueError("PUBLIC_PAGE_CHUNK_MAPPING_NOT_FOUND")
    url=ROOT+"/static/js/"+NAME+"."+m.group(1)+".js"
    js=get(url)
    selected={}
    for marker in ("matchInfoCode","getSpHistorys","getJcOddsDetail","rqspf","spf","onLoad:function","created:function"):
        matches=list(re.finditer(re.escape(marker),js,re.I))
        selected[marker]={"occurrences":len(matches),"contexts":[
            js[max(0,x.start()-500):min(len(js),x.end()+1600)][:2200] for x in matches[:6]]}
    data={"checked_bj":dt.datetime.now(TZ).isoformat(),"url":url,"source":"public Caidao H5 compiled JS",
          "raw_js_archived":False,"field_traces":selected}
    folder=pathlib.Path("mfm-data/source-diagnostics");folder.mkdir(parents=True,exist_ok=True)
    path=folder/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_spchange_code.json")
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(path),"hits":{k:v["occurrences"] for k,v in selected.items()}},ensure_ascii=False))
if __name__=="__main__":main()
