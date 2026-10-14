#!/usr/bin/env python3
"""Read-only, unauthenticated public H5 API contract probe.

Only data-read methods observed in a publicly delivered JS bundle. One request
per endpoint; no credentials, no bypass, no login automation, no bulk access.
Never save response bodies that might contain account data.
"""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

ROOT = "http://zk.bjjckx.com"
TZ = ZoneInfo("Asia/Shanghai")
PATHS = [
    "/api/web/game/getLeagueMatchList",
    "/api/web/game/getWorldCupOddsList",
    "/api/web/game/getSpfzstdetail",
    "/api/web/game/getRqSpfzstdetail",
    "/api/web/game/getJcZstDetail",
]
def probe():
    out = {"retrieved_at_bj": dt.datetime.now(TZ).isoformat(),
           "h5_origin": ROOT, "requests": [],
           "no_credentials_or_access_bypass": True,
           "no_personal_response_data_saved": True}
    for path in PATHS:
        info = {"path": path, "request_method": "POST",
                "parameters": "empty_probe_only"}
        req = urllib.request.Request(ROOT + path, data=b"",
                headers={"User-Agent": "MFM-public-H5-contract-test/1.0",
                         "Referer": ROOT + "/",
                         "Accept": "application/json, text/plain, */*",
                         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST")
        try:
            with urllib.request.urlopen(req, timeout=9) as response:
                info["http_status"] = response.status
                info["content_type"] = response.headers.get("Content-Type","")
                raw = response.read(160_001)
                info["response_bytes_capped"] = len(raw)
            try:
                payload = json.loads(raw)
                info["response_kind"] = "json"
                if isinstance(payload, dict):
                    info["top_level_keys"] = sorted(payload)[:25]
                    # Only status-like fields; never output response arrays/user data
                    for key in ("code", "status", "success", "errCode"):
                        if key in payload and isinstance(payload[key], (bool, int, str)):
                            info[key] = str(payload[key])[:70]
            except (ValueError, UnicodeError):
                info["response_kind"] = "html_or_other"
        except urllib.error.HTTPError as exc:
            info.update({"http_status": exc.code, "error_type": "HTTPError"})
            if exc.code in (401,403,429,567):
                out["requests"].append(info)
                out["status"] = "ACCESS_RESTRICTED_STOPPED"
                break
        except (OSError, ValueError) as exc:
            info.update({"error_type": type(exc).__name__, "error": str(exc)[:160]})
        out["requests"].append(info)
    return out

if __name__ == "__main__":
    out = pathlib.Path("mfm-data/source-diagnostics")
    out.mkdir(parents=True, exist_ok=True)
    result = probe()
    path = out / (dt.datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z") + "_caidao_api.json")
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(path),"probed":len(result["requests"]),
                      "http_statuses":[x.get("http_status") for x in result["requests"]]},ensure_ascii=False))
