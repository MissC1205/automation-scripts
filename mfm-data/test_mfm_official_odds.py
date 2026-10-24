"""Offline contract tests for official SP probe, no network required."""
import importlib.util
import json
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("mfm_official_odds", pathlib.Path(__file__).with_name("mfm_official_odds.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Response:
    def __init__(self, body, content_type="application/json"):
        self.body = body
        self.status = 200
        self.headers = {"Content-Type": content_type}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return self.body[:n]

class TestContract(unittest.TestCase):
    def test_valid_market_and_query(self):
        raw = {"value": {"matchInfoList": [{"subMatchList": [
            {"matchId": 1, "matchNumStr": "周三011", "home": {"abbName": "曼城"},
             "away": {"abbName": "巴黎"}, "odds": {
                 "had": {"h": "1.88", "d": "3.75", "a": "3.02"},
                 "hhad": {"goalLine": -1, "h": "3.5", "d": "3.8", "a": "1.75"}}},
            {"matchId": 2, "odds": {"had": {"h": None, "d": "3", "a": "4"}}}
        ]}]}}
        def opener(request, timeout):
            self.assertIn("channel=c", request.full_url)
            self.assertIn("poolCode=had%2Chhad", request.full_url)
            return Response(json.dumps(raw).encode())
        result = mod.probe(opener=opener)
        self.assertEqual(result["status"], "VALID_SP_ROWS_AVAILABLE_IDENTITY_REQUIRES_CROSSCHECK")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["markets"]["hhad"]["integer_handicap"], -1)
        self.assertFalse(result["official_sale_list_verified"])

    def test_unexpected_json_fails(self):
        result = mod.probe(opener=lambda request, timeout: Response(b'{"hello":true}'))
        self.assertEqual(result["status"], "SCHEMA_ERROR")
        self.assertEqual(result["matches"], [])

    def test_html_waf_fails(self):
        result = mod.probe(opener=lambda request, timeout: Response(b"<html>blocked</html>", "text/html"))
        self.assertEqual(result["status"], "SCHEMA_ERROR")

    def test_dns_fails_explicitly(self):
        def fail(request, timeout): raise OSError("Temporary failure in name resolution")
        result = mod.probe(opener=fail)
        self.assertEqual(result["status"], "SOURCE_FAILURE")
        self.assertEqual(result["sources"]["calculator"]["error_type"], "OSError")

if __name__ == "__main__": unittest.main()
