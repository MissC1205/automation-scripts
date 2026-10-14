#!/usr/bin/env python3
"""Source-stamped official JC fixed-odds probe; never treats JSON alone as valid SP."""
import datetime as dt
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
BASE = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"
POOLS = "had,hhad,crs,ttg,hafu"
HEADERS = {
    "User-Agent": "MFM-source-audit/2.0 (+public-football-data-research)",
    "Referer": "https://m.sporttery.cn/mjc/jsq/zqspf/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def market_values(item):
    odds = item.get("odds") if isinstance(item, dict) else None
    if not isinstance(odds, dict):
        return {}
    found = {}
    for pool in ("had", "hhad"):
        values = odds.get(pool)
        if not isinstance(values, dict):
            continue
        try:
            prices = [float(values[k]) for k in ("h", "d", "a")]
        except (TypeError, ValueError, KeyError):
            continue
        if not all(1.0 < v < 1000 for v in prices):
            continue
        found[pool] = {
            "home": prices[0], "draw": prices[1], "away": prices[2],
            "update_time_raw": values.get("updateTime"),
        }
        if pool == "hhad":
            line = values.get("goalLineValue", values.get("goalLine"))
            try:
                if line is not None:
                    found[pool]["integer_handicap"] = int(line)
            except (ValueError, TypeError):
                pass
    return found

def parse_response(payload):
    if not isinstance(payload, dict):
        raise ValueError("ROOT_NOT_OBJECT")
    value = payload.get("value")
    groups = value.get("matchInfoList") if isinstance(value, dict) else None
    if not isinstance(groups, list):
        raise ValueError("SCHEMA_MISMATCH_value.matchInfoList")
    rows = []
    for group in groups:
        if isinstance(group, dict):
            rows.extend(x for x in (group.get("subMatchList") or []) if isinstance(x, dict))
    valid = []
    for row in rows:
        markets = market_values(row)
        if markets:
            home = row.get("home")
            away = row.get("away")
            valid.append({
                "match_id": row.get("matchId", row.get("id")),
                "match_no": row.get("matchNumStr"),
                "home": home.get("abbName") if isinstance(home, dict) else home,
                "away": away.get("abbName") if isinstance(away, dict) else away,
                "markets": markets,
            })
    return {"raw_match_count": len(rows),
            "matches_with_valid_1x2_or_handicap": len(valid), "matches": valid}

def probe(*, now=None, opener=None):
    now = now or dt.datetime.now(TZ)
    opener = opener or urllib.request.urlopen
    url = BASE + "?" + urllib.parse.urlencode({"channel": "c", "poolCode": POOLS})
    result = {
        "collected_at": now.isoformat(), "source": "sporttery.cn", "source_url": url,
        "official_sale_list_verified": False, "status": "SOURCE_FAILURE",
        "matches": [], "sources": {"calculator": {"url": url}},
        "history": {"status": "NOT_PROBED",
                    "reason": "Requires validated event-specific query schema; no naked history requests"},
    }
    entry = result["sources"]["calculator"]
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with opener(req, timeout=15) as response:
            entry["http_status"] = response.status
            entry["content_type"] = response.headers.get("Content-Type", "")
            body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise ValueError("PAYLOAD_SIZE_LIMIT")
        if body.lstrip().startswith(b"<"):
            raise ValueError("HTML_OR_WAF_RESPONSE_NOT_JSON")
        parsed = parse_response(json.loads(body))
        entry.update({
            "raw_match_count": parsed["raw_match_count"],
            "matches_with_valid_1x2_or_handicap": parsed["matches_with_valid_1x2_or_handicap"],
        })
        result["matches"] = parsed["matches"]
        result["status"] = ("VALID_SP_ROWS_AVAILABLE_IDENTITY_REQUIRES_CROSSCHECK"
                            if result["matches"] else "NO_VALID_SP_ROWS")
    except urllib.error.HTTPError as exc:
        entry.update({"http_status": exc.code, "error_type": "HTTPError", "error": str(exc)[:200]})
        result["status"] = ("ACCESS_DENIED_OR_UPSTREAM_ERROR" if exc.code in (401, 403, 429, 567)
                            else "SOURCE_FAILURE")
    except (OSError, ValueError) as exc:
        entry.update({"error_type": type(exc).__name__, "error": str(exc)[:200]})
        result["status"] = ("SCHEMA_ERROR" if isinstance(exc, ValueError)
                            and not isinstance(exc, json.JSONDecodeError) else "SOURCE_FAILURE")
    return result

def main():
    now = dt.datetime.now(TZ)
    base = pathlib.Path(os.environ.get("MFM_ODDS_OUTPUT_DIR", "mfm-data/official-odds")) / now.strftime("%Y-%m-%d")
    base.mkdir(parents=True, exist_ok=True)
    result = probe(now=now)
    path = base / (now.strftime("%Y%m%dT%H%M%S%z") + ".json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "file": str(path), "status": result["status"],
        "valid_market_matches": len(result["matches"]),
        "calculator": {k: v for k, v in result["sources"]["calculator"].items()
                       if k in ("http_status", "error_type", "raw_match_count")},
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
