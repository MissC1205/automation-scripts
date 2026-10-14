#!/usr/bin/env python3
"""Inspect public Caidao H5 assets; do not bypass authentication or WAF."""
import datetime as dt
import html.parser
import json
import pathlib
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

DOMAIN = "zk.bjjckx.com"
TZ = ZoneInfo("Asia/Shanghai")
ROOTS = ("https://" + DOMAIN + "/", "http://" + DOMAIN + "/")

class Scripts(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.srcs = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            src = dict(attrs).get("src")
            if src:
                self.srcs.append(src)

def get(url, cap=400000):
    req = urllib.request.Request(url, headers={
        "User-Agent": "MFM public-web source diagnostic/1.0",
        "Accept": "text/html,application/javascript,*/*"
    })
    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read(cap + 1)
        return {"status": resp.status, "url": resp.geturl(),
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes_read": min(len(raw), cap),
                "truncated": len(raw) > cap}, raw[:cap]

def run():
    out = {"retrieved_at_bj": dt.datetime.now(TZ).isoformat(),
           "domain": DOMAIN, "client_hash_route_not_sent_in_HTTP": True,
           "no_credentials_or_access_bypass": True,
           "dns": {}, "landing": [], "js_assets": [], "endpoint_status": "UNVERIFIED"}
    try:
        out["dns"] = {"status": "resolved",
                      "addresses": sorted({a[4][0] for a in socket.getaddrinfo(DOMAIN, None)})[:5]}
    except OSError as exc:
        out["dns"] = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)[:180]}
    for url in ROOTS:
        try:
            meta, body = get(url)
            out["landing"].append(meta)
            if "html" not in meta["content_type"].lower() and b"<html" not in body[:500].lower():
                continue
            parser = Scripts()
            parser.feed(body.decode("utf-8", errors="replace"))
            scripts = []
            for src in parser.srcs:
                resolved = urllib.parse.urljoin(meta["url"], src)
                u = urllib.parse.urlsplit(resolved)
                if u.hostname == DOMAIN and u.scheme in ("http", "https"):
                    public = urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, "", ""))
                    if public not in scripts:
                        scripts.append(public)
            out["public_same_origin_js"] = scripts[:8]
            for src in scripts[:3]:
                try:
                    asset, raw = get(src)
                    asset["api_path_candidates_unverified"] = sorted(set(
                        re.findall(r"/(?:api|gateway|football|match|sports)/[A-Za-z0-9_./-]{3,100}",
                                   raw.decode("utf-8", errors="replace"))))[:40]
                    out["js_assets"].append(asset)
                except (OSError, ValueError) as exc:
                    out["js_assets"].append({"url": src, "error_type": type(exc).__name__, "error": str(exc)[:180]})
            break
        except urllib.error.HTTPError as exc:
            out["landing"].append({"url": url, "http_status": exc.code, "error_type": "HTTPError"})
            if exc.code in (401, 403, 429, 567):
                out["endpoint_status"] = "ACCESS_RESTRICTED_DO_NOT_RETRY"
                break
        except (OSError, ValueError) as exc:
            out["landing"].append({"url": url, "error_type": type(exc).__name__, "error": str(exc)[:180]})
    if any(x.get("status") == 200 for x in out["landing"]):
        out["endpoint_status"] = "PUBLIC_LANDING_ACCESSIBLE_JS_UNVERIFIED"
    return out

if __name__ == "__main__":
    out = pathlib.Path("mfm-data/source-diagnostics")
    out.mkdir(parents=True, exist_ok=True)
    result = run()
    target = out / (dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z") + "_caidao.json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"saved": str(target), "dns_status": result["dns"]["status"],
                      "site_status": result["endpoint_status"],
                      "js_assets": len(result["js_assets"])}, ensure_ascii=False))
