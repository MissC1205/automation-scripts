"""Offline regression checks for read-only Caidao SPF historical data."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from zoneinfo import ZoneInfo

FILE=pathlib.Path(__file__).with_name("mfm_caidao_history.py")
spec=importlib.util.spec_from_file_location("caidao_history",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW=dt.datetime(2026,10,14,18,30,tzinfo=ZoneInfo("Asia/Shanghai"))
FIXTURE={"matchInfo":"F20261014011","matchNum":"周三011",
         "hostTeam":"曼城","guestTeam":"巴黎圣曼"}
BASE={"status":200,"message":"成功","result":{
    "matchNum":"周三011","hostTeam":"曼城","guestTeam":"巴黎圣曼",
    "wf":"spf","concedeNum":"-1",
    "oddsDetails":[
        {"updateTime":"2026-10-14 17:49:22","odds":"1.83|3.80|3.13","oddsflag":"-1|1|1","num":""},
        {"updateTime":"2026-10-13 09:41:32","odds":"2.11|3.60|2.65","oddsflag":"0|0|0","num":""},
    ]}}

class TestHistory(unittest.TestCase):
    def test_prices(self):
        self.assertEqual(mod.parse_prices("3.40|3.88|1.73")["away"],1.73)
        self.assertIsNone(mod.parse_prices("3.40|X|1.73"))
        self.assertIsNone(mod.parse_prices("3.40|3.88"))
    def test_order_and_identity(self):
        data=mod.parse_history(BASE,FIXTURE,NOW)
        self.assertTrue(data["verified_for_model_use"])
        self.assertEqual(data["history_count"],2)
        self.assertEqual(data["history"][0]["home"],2.11)
        self.assertEqual(data["history"][-1]["home"],1.83)
        self.assertEqual(data["market"],"spf")
    def test_wrong_match_is_not_verified(self):
        fixture=dict(FIXTURE,guestTeam="错误球队")
        self.assertFalse(mod.parse_history(BASE,fixture,NOW)["verified_for_model_use"])
    def test_invalid_time_and_duplicate_rejected(self):
        bad={"status":200,"result":dict(BASE["result"])}
        bad["result"]["oddsDetails"]=list(BASE["result"]["oddsDetails"])+[
          {"updateTime":"2026-10-14 17:49:22","odds":"1.83|3.80|3.13"}]
        data=mod.parse_history(bad,FIXTURE,NOW)
        self.assertEqual(data["duplicate_timestamps"],1)
        self.assertFalse(data["verified_for_model_use"])

if __name__=="__main__":
    unittest.main()
