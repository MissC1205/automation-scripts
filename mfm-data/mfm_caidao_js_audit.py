#!/usr/bin/env python3
"""Static inspection of publicly served Caidao H5 JS; no bypass or login."""
import datetime as dt
import html.parser
import json
import pathlib
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

DOMAIN = "zk.bjjckx.com"
ROOT = "http://" + DOMAIN + "/"
TZ = ZoneInfo("Asia/Shanghai")
HEADERS = {"User-Agent": "MFM-public-H5-audit/1.0"}

class Scripts(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            src = dict(attrs).get("src")
            if src:
                self.urls.append(src)

def fetch(url, cap=3_000_000):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=15) as r:
        body = r.read(cap + 1)
        return body[:cap], len(body) > cap

def run():
    out = {"captured_at_bj": dt.datetime.now(TZ).isoformat(),
           "source": ROOT,
           "read_only_public_assets": True, "no_unverified_endpoint_calls": True,
           "bundle_results": []}
    html, _ = fetch(ROOT, 50_000)
    p = Scripts()
    p.feed(html.decode("utf-8", errors="replace"))
    assets = []
    for src in p.urls:
        full = urllib.parse.urljoin(ROOT, src)
        if urllib.parse.urlparse(full).hostname == DOMAIN:
            assets.append(full)
    for url in assets[:4]:
        row = {"url": url}
        try:
            data, truncated = fetch(url)
            js = data.decode("utf-8", errors="replace")
            row.update({"bytes": len(data), "truncated": truncated,
                        "api_path_literals": sorted(set(re.findall(
                            r"/(?:api|gateway)/[A-Za-z0-9_./?=&%-]{3,140}", js)))[:120],
                        "http_hosts": sorted(set(re.findall(
                            r"https?://([A-Za-z0-9.-]+)", js)))[:80]})
            # Markers suggest the route/HTTP client machinery; only store
            # small, redacted contexts, never entire proprietary bundle.
            contexts = []
            for marker in ("/api/web/game", "baseURL", "axios.create", "football-detail",
                           "apiUrl", "request.get", "request.post", "footballDetail"):
                for m in list(re.finditer(re.escape(marker), js, flags=re.IGNORECASE))[:4]:
                    seg = js[max(0, m.start()-110):m.end()+160].replace("\n", " ")
                    seg = re.sub(r"(?i)(token|secret|password|authorization|api[-_]?key)[^;,}]{0,90}",
                                 "[REDACTED_SENSITIVE_KEY_CONTEXT]", seg)
                    contexts.append({"marker": marker, "offset": m.start(), "fragment": seg[:300]})
            row["selected_js_contexts"] = contexts[:30]
            game_start = js.find('"/api/web/game"')
            if game_start >= 0:
                service_module = js[game_start:game_start + 14000]
                row["game_service_methods_unverified"] = [
                    {"method_name": name, "http_path": "/api/web/game" + suffix}
                    for name, suffix in re.findall(
                        r'([A-Za-z_]\w*):function\([^)]*\)\{return [^{}]{0,180}?o\+"([^"]+)"',
                        service_module
                    )
                ][:80]
            row["base_url_literals_unverified"] = sorted(set(
                re.findall(r"BASE_URL\s*:\s*['\"](https?://[A-Za-z0-9.:-]+)", js)
            ))[:20]
            callsites = []
            for name in ("getSpfzstdetail", "getRqSpfzstdetail", "getJcZstDetail",
                         "getLeagueMatchList", "getWorldCupOddsList"):
                for m in list(re.finditer(re.escape(name), js))[:10]:
                    seg = js[max(0,m.start()-190):m.end()+210]
                    seg = re.sub(r"(?i)(token|secret|password|authorization|api[-_]?key)[^;,}]{0,90}",
                                 "[REDACTED]", seg)
                    callsites.append({"name":name, "offset":m.start(), "context":seg[:400]})
            row["read_endpoint_callsite_contexts"] = callsites[:35]
        except (OSError, ValueError) as e:
            row["error_type"] = type(e).__name__
            row["error"] = str(e)[:180]
        out["bundle_results"].append(row)
    return out

if __name__ == "__main__":
    out = pathlib.Path("mfm-data/source-diagnostics")
    out.mkdir(parents=True, exist_ok=True)
    data = run()
    path = out / (dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z") + "_caidao_js.json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"file": str(path), "bundles": len(data["bundle_results"]),
                      "paths_found": sum(len(x.get("api_path_literals", [])) for x in data["bundle_results"])}, ensure_ascii=False))
