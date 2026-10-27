"""Offline checks for transient ESPN enrichment failures."""
import io
import unittest
import urllib.error
from unittest.mock import patch
import mfm_enrich

class EnrichFetchTests(unittest.TestCase):
 def test_ssl_handshake_timeout_retries_once(self):
  transient=urllib.error.URLError(TimeoutError("The handshake operation timed out"))
  with patch.object(mfm_enrich.urllib.request,"urlopen",side_effect=[transient,io.BytesIO(b'{"ok":true}')]) as mocked, patch.object(mfm_enrich.time,"sleep"):
   self.assertEqual(mfm_enrich.fetch("https://example.test/summary"),{"ok":True})
   self.assertEqual(mocked.call_count,2)

 def test_http_567_does_not_retry(self):
  error=urllib.error.HTTPError("https://example.test/summary",567,"Unknown Status",None,None)
  with patch.object(mfm_enrich.urllib.request,"urlopen",side_effect=error) as mocked, patch.object(mfm_enrich.time,"sleep"):
   with self.assertRaises(urllib.error.HTTPError):
    mfm_enrich.fetch("https://example.test/summary")
   self.assertEqual(mocked.call_count,1)

 def test_two_timeouts_remain_failure(self):
  transient=urllib.error.URLError(TimeoutError("timed out"))
  with patch.object(mfm_enrich.urllib.request,"urlopen",side_effect=[transient,transient]) as mocked, patch.object(mfm_enrich.time,"sleep"):
   with self.assertRaises(urllib.error.URLError):
    mfm_enrich.fetch("https://example.test/summary")
   self.assertEqual(mocked.call_count,2)

if __name__=="__main__":unittest.main()
