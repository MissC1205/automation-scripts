#!/usr/bin/env python3
"""Focused public-code inspection: getMatchList request construction only."""
import datetime as dt,json,pathlib,re,urllib.request
from zoneinfo import ZoneInfo
TZ=ZoneInfo("Asia/Shanghai")
ASSETS={
    "football_index":"http://zk.bjjckx.com/static/js/package-analysis-match-live-football-football-index-football-index.dff2060b.js",
    "football_detail":"http://zk.bjjckx.com/static/js/package-analysis-match-live-football-football-detail-football-detail.702cfbf0.js",
    "app_index":"http://zk.bjjckx.com/static/js/index.e98df7de.js",
    "match_analysis":"http://zk.bjjckx.com/static/js/pages-index-match-analysis-match-analysis.27ff7b82.js",
}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"MFM-public-static-code-inspection/1.0"}),timeout=12) as resp:
        raw=resp.read(900000)
    return raw.decode("utf-8",errors="replace")
def search(text,needle,before=200,after=2900,cap=3):
    return [{"offset":m.start(),"snippet":text[max(0,m.start()-before):m.end()+after]}
            for m in list(re.finditer(re.escape(needle),text))[:cap]]
def go():
    output={"inspected_at_bj":dt.datetime.now(TZ).isoformat(),"assets":{},"public_js_only":True}
    for name,url in ASSETS.items():
        try:
            js=get(url)
            queries={
                "getMatchList_code":search(js,"getMatchList:function",150,3700,2),
                "footballQuery_service":search(js,"getScoresLive:function",120,500,2),
                "getSpfzstdetail_service":search(js,"getSpfzstdetail:function",120,450,2),
                "footballQuery_literal":search(js,"footballQuery",200,800,2),
                "request_args":search(js,"getScoresLive",300,1200,5),
                "fixture_request":search(js,"getMatchAnalysis",200,900,3),
                "page_load":search(js,"onShow:function",100,500,2),
            }
            output["assets"][name]={"url":url,"bytes":len(js),"queries":{k:v for k,v in queries.items() if v}}
        except (OSError,ValueError) as e:output["assets"][name]={"url":url,"error":str(e)[:200]}
    return output
if __name__=="__main__":
    o=go()
    root=pathlib.Path("mfm-data/source-diagnostics")
    root.mkdir(parents=True,exist_ok=True)
    path=root/(dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")+"_caidao_focus.json")
    path.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(path),"assets":{k:("error" if "error" in v else list(v["queries"])) for k,v in o["assets"].items()}},ensure_ascii=False))
