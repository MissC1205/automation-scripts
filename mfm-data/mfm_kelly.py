#!/usr/bin/env python3
"""MFM Kelly shadow analysis. Never derives independent match predictions from odds."""
from __future__ import annotations
import math
from statistics import pstdev

OUTCOMES = ("home", "draw", "away")

def _prices(row):
    if not isinstance(row, dict) or set(row) != set(OUTCOMES):
        raise ValueError("require home/draw/away odds")
    values = {k: float(row[k]) for k in OUTCOMES}
    if not all(math.isfinite(v) and 1 < v < 1000 for v in values.values()):
        raise ValueError("odds must be finite decimal values >1 and <1000")
    return values

def _probabilities(row):
    if not isinstance(row, dict) or set(row) != set(OUTCOMES):
        raise ValueError("require home/draw/away probabilities")
    values = {k: float(row[k]) for k in OUTCOMES}
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values.values()):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(values.values()) - 1) > 1e-6:
        raise ValueError("probabilities must sum to one")
    return values

def no_vig_market_probabilities(odds):
    """Single-source market benchmark; NEVER an independent forecast."""
    prices = _prices(odds)
    inv = {k: 1 / v for k, v in prices.items()}
    total = sum(inv.values())
    return {k: inv[k] / total for k in OUTCOMES}

def bookmaker_indices(books, *, distinct_bookmakers_verified=False):
    """Descriptive index: bookmaker odds times leave-one-out market p.
    Only for >=2 independently identified bookmakers; no win-probability claim.
    """
    if not distinct_bookmakers_verified:
        return {"status": "UNAVAILABLE_UNVERIFIED_BOOKMAKER_IDENTITY", "indices": None}
    if not isinstance(books, dict) or len(books) < 2:
        return {"status": "UNAVAILABLE_NEEDS_TWO_DISTINCT_BOOKMAKERS", "indices": None}
    try:
        validated = {name: _prices(odds) for name, odds in books.items()
                     if isinstance(name, str) and name.strip()}
        if len(validated) != len(books):
            raise ValueError("invalid bookmaker name")
    except (TypeError, ValueError, OverflowError) as exc:
        return {"status": "INVALID_ODDS", "indices": None, "reason": str(exc)}
    results = {}
    for name, prices in validated.items():
        other = [no_vig_market_probabilities(row)
                 for key, row in validated.items() if key != name]
        benchmark = {k: sum(p[k] for p in other) / len(other) for k in OUTCOMES}
        results[name] = {k: round(prices[k] * benchmark[k], 6) for k in OUTCOMES}
    dispersion = {k: round(pstdev([r[k] for r in results.values()]), 6)
                  for k in OUTCOMES}
    return {"status": "SHADOW_MARKET_ONLY", "convention": "leave_one_out_market_benchmark",
            "indices": results, "dispersion": dispersion,
            "not_forecast_probabilities": True}

def kelly_stake(probability, decimal_odds, *, calibrated=False,
                forecast_frozen_before_market=False, official_sp_verified=False,
                cap=0.01, fractional_kelly=0.25):
    """Research-only fractional Kelly. A blocked gate never returns a stake."""
    if not (calibrated and forecast_frozen_before_market and official_sp_verified):
        return {"status": "BLOCKED_UNVERIFIED_PROBABILITY_OR_OFFICIAL_SP",
                "full_kelly": None, "suggested_fraction": None}
    try:
        p, d, limit, multiplier = map(float, (probability, decimal_odds, cap, fractional_kelly))
    except (TypeError, ValueError, OverflowError):
        return {"status": "INVALID_INPUT", "full_kelly": None, "suggested_fraction": None}
    if not (math.isfinite(p) and 0 <= p <= 1 and math.isfinite(d) and 1 < d < 1000
            and math.isfinite(limit) and 0 < limit <= 0.01
            and math.isfinite(multiplier) and 0 < multiplier <= 0.25):
        return {"status": "INVALID_INPUT", "full_kelly": None, "suggested_fraction": None}
    ev = p * d - 1
    if ev <= 0:
        return {"status": "NON_POSITIVE_EV_NO_BET", "ev_per_unit": ev,
                "full_kelly": 0.0, "suggested_fraction": 0.0}
    full = ev / (d - 1)
    return {"status": "RESEARCH_ONLY_NOT_BETTING_INSTRUCTION", "ev_per_unit": ev,
            "full_kelly": full, "suggested_fraction": min(full * multiplier, limit),
            "fractional_kelly": multiplier, "cap": limit}

def market_snapshot_shadow(market_only):
    """Annotate Caidao snapshots without inventing a bookmaker index or EV."""
    matches = market_only.get("matches", [])
    if not isinstance(matches, list):
        raise ValueError("expected matches list")
    rows = []
    for m in matches:
        if not isinstance(m, dict):
            continue
        odds = m.get("market", {}).get("spf")
        try:
            baseline = no_vig_market_probabilities(odds)
            status = "THIRD_PARTY_MARKET_BENCHMARK_ONLY"
        except (TypeError, ValueError, OverflowError):
            baseline = None
            status = "MISSING_OR_INVALID_SPF"
        rows.append({"match_id": m.get("match_id"), "jc_number": m.get("jc_number"),
                     "market_only_no_vig_probabilities": baseline, "market_status": status,
                     "bookmaker_kelly_status": "UNAVAILABLE_NEEDS_VERIFIED_MULTI_BOOKMAKER_QUOTES",
                     "stake_kelly_status": "BLOCKED_REQUIRES_FROZEN_CALIBRATED_MODEL_AND_OFFICIAL_SP"})
    return {"sale_date_bj": market_only.get("sale_date_bj"),
            "source": "Caidao THIRD_PARTY_NOT_OFFICIAL",
            "analysis_mode": "SHADOW_MARKET_ONLY_NO_PREDICTION", "matches": rows}
