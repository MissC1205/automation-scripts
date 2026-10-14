"""Offline MFM operational Caidao quality gate tests (no network or credentials)."""
import datetime as dt
import importlib.util
import pathlib
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("mfm_caidao_service",ROOT/"mfm_caidao_service.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
FIXED=dt.datetime(2026,10,14,18,22,0,tzinfo=ZoneInfo("Asia/Shanghai"))
def fixtures():
    return [
      {"matchInfo":"F20261014008","matchNum":"周三008",
       "hostTeam":"罗马","guestTeam":"皇马","matchName":"欧冠",
       "gameTime":"20261015030000","spfOdds":"3.45|3.92|1.71",
       "concedeNum":1,"rqspfOdds":"1.87|3.90|2.96",
       "zjqOdds":"27.00|8.50|4.90|3.65|4.40|6.25|10.00|12.00"},
      {"matchInfo":"F20261014004","matchNum":"周三004",
       "hostTeam":"横滨水手","guestTeam":"清水鼓动","matchName":"日联赛杯",
       "gameTime":"20261014180000","spfOdds":"1.9|3.2|3.45",
       "concedeNum":-1,"rqspfOdds":"4.10|3.6|1.65"}
    ]
def transport(path,params,method="GET"):
    if path.endswith("footballQuery"):
        return {"status":200,"body":fixtures() if params["type"]==0 else []}
    if path.endswith("getMatchAllData"):
        return {"status":200,"data":{
            "matchFeatureStr":'{"last":{"home":"1-2-3"},"goalAvg":{"home":1.4}}',
            "historyDataStr":'{"matchList":[],"statistics":{}}',
            "injurySuspensionStr":'{"home":[],"away":[]}',
            "updateTime":"2026-10-14 17:33:00",
            "poissonDistributionStr":'{"spfsExp":99.9,"spfpExp":0.05}' }}
    if path.endswith("getJcOddsDetail"):
        f=next(x for x in fixtures() if x["matchInfo"]==params["matchInfo"])
        return {"status":200,"result":{
            "matchNum":f["matchNum"],"hostTeam":f["hostTeam"],"guestTeam":f["guestTeam"],
            "wf":"spf","concedeNum":str(f["concedeNum"]),
            "oddsDetails":[{"updateTime":"2026-10-14 17:10:05","odds":f["spfOdds"],
                            "oddsflag":"0|0|0","num":""}]}}
    raise AssertionError("unexpected route "+path)

class CaidaoServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous=mod.utc_bj_now
        mod.utc_bj_now=lambda: FIXED
    @classmethod
    def tearDownClass(cls):
        mod.utc_bj_now=cls.previous
    def test_identity_and_market_distinction(self):
        self.assertTrue(mod.match_identity_valid("F20261014008","2026-10-14"))
        self.assertFalse(mod.match_identity_valid("F20261013008","2026-10-14"))
        parsed=mod.market_prices(fixtures()[0])
        self.assertEqual(parsed["spf"]["away"],1.71)
        self.assertEqual(parsed["integer_handicap"],1)
        self.assertEqual(parsed["handicap_sp"]["home"],1.87)
        self.assertIsNone(mod.market_prices({})["handicap_sp"])
    def test_collector_and_no_vendor_prediction(self):
        report=mod.collect("2026-10-14",now=FIXED,transport=transport,pause=lambda x:None)
        coverage=report["coverage"]
        self.assertEqual(coverage["fixture_ids"],2)
        self.assertEqual(coverage["historical_spf_matches_verified"],2)
        self.assertEqual(coverage["detail_objects"],2)
        self.assertEqual(coverage["captured_before_kickoff"],1)
        self.assertEqual(coverage["captured_after_kickoff"],1)
        self.assertEqual(coverage["prematch_verified_history_snapshots"],1)
        self.assertEqual(report["quality_gate"],"RESEARCH_DATA_AVAILABLE")
        self.assertIn("BLOCKED",report["betting_gate"])
        match=report["matches"][0]
        self.assertTrue(match["model_features"]["vendor_prediction_outputs_excluded"])
        self.assertNotIn("poissonDistributionStr",match["model_features"]["usable_as_third_party_research_inputs"])
    def test_persistent_files(self):
        report=mod.collect("2026-10-14",now=FIXED,transport=transport,pause=lambda x:None)
        with tempfile.TemporaryDirectory() as temp:
            path=mod.persist(report,temp)
            self.assertTrue(path.exists())
            self.assertTrue((path.parent/"latest.json").exists())
            self.assertTrue((path.parent/"summary.json").exists())
            self.assertTrue((pathlib.Path(temp)/"latest-summary.json").exists())
    def test_missing_data_marks_partial(self):
        def no_detail(path,params,method="GET"):
            if path.endswith("getMatchAllData"):
                return {"status":200,"data":None}
            return transport(path,params,method)
        report=mod.collect("2026-10-14",now=FIXED,transport=no_detail,pause=lambda x:None)
        self.assertEqual(report["quality_gate"],"PARTIAL_RESEARCH_DATA")
        self.assertEqual(report["coverage"]["detail_objects"],0)
    def test_source_dates_do_not_replace_capture_dates(self):
        report=mod.collect("2026-10-14",now=FIXED,transport=transport,pause=lambda x:None)
        four=next(x for x in report["matches"] if x["jc_number"]=="周三004")
        self.assertEqual(four["collection_phase"],"POST_KICKOFF")
        self.assertFalse(four["data_quality"]["true_prematch_snapshot"])
        self.assertTrue(four["spf_history"]["verified_for_model_use"])
if __name__=="__main__":
    unittest.main()
