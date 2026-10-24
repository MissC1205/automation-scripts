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
    "/api/web/game/footballQuery",
    "/api/web/game/footballLiveQuery",
]
def probe():
    out = {"retrieved_at_bj": dt.datetime.now(TZ).isoformat(),
           "h5_origin": ROOT, "requests": [],
           "no_credentials_or_access_bypass": True,
           "no_personal_response_data_saved": True}
    for path in PATHS:
        method = "GET" if path.endswith("/footballQuery") else "POST"
        info = {"path": path, "request_method": method,
                "parameters": "empty_probe_only"}
        req = urllib.request.Request(ROOT + path, data=None if method == "GET" else b"",
                headers={"User-Agent": "MFM-public-H5-contract-test/1.0",
                         "Referer": ROOT + "/",
                         "Accept": "application/json, text/plain, */*",
                         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method=method)
        try:
            with urllib.request.urlopen(req, timeout=9) as response:
                info["http_status"] = response.status
                info["content_type"] = response.headers.get("Content-Type","")
                raw = response.read(160_001)
                info["response_bytes_capped"] = len(raw)
                info["response_truncated"] = len(raw) > 160_000
            try:
                payload = json.loads(raw)
                info["response_kind"] = "json"
                if isinstance(payload, dict):
                    info["top_level_keys"] = sorted(payload)[:25]
                    # Only public aggregate metadata; never persist response arrays or user data.
                    for key in ("code", "status", "success", "errCode"):
                        if key in payload and isinstance(payload[key], (bool, int, str)):
                            info[key] = str(payload[key])[:70]
                    message = payload.get("message")
                    if isinstance(message, str):
                        info["public_error_message"] = message[:110]
                    data = payload.get("data")
                    info["data_kind"] = type(data).__name__
                    if isinstance(data, str):
                        info["data_string_length"] = len(data)
                        try:
                            inner = json.loads(data)
                            info["data_string_json_kind"] = type(inner).__name__
                            if isinstance(inner, list):
                                info["data_string_json_row_count"] = len(inner)
                            elif isinstance(inner, dict):
                                info["data_string_json_keys_only"] = sorted(inner)[:30]
                        except (ValueError, TypeError):
                            pass
                    if isinstance(data, list):
                        info["data_row_count"] = len(data)
                        if data and isinstance(data[0], dict):
                            info["first_row_fields_only"] = sorted(data[0])[:50]
                    elif isinstance(data, dict):
                        info["data_fields_only"] = sorted(data)[:50]
                        info["nested_collection_counts"] = {
                            k: len(v) for k, v in data.items()
                            if isinstance(v, list) and not any(
                                word in k.lower() for word in ("user", "phone", "customer", "member")
                            )
                        }
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
