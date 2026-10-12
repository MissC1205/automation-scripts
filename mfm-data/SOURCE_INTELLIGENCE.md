# MFM Source Intelligence Registry (v1.0, 2026-10-12)

## Mandatory rules
- Each new information item must include: source_name, source_url, retrieved_at_utc, published_at_utc (if available), event_id, home/away, competition, raw_value, normalized_value, field, source_tier, verification_status, licence_status, and notes.
- Source tiers: A official league/lottery, B first-party statistics/data provider, C secondary aggregators, D commentary or unsupported claims.
- Never treat an HTTP 200 response as proof of a usable field. Record coverage, missingness, freshness, and conflicts; do not silently fill missing data.
- For betting odds capture bookmaker, market, line, decimal price, observed_at, opening/closing distinction and time zone. Official Chinese JC SP and handicap are a separate feed.
- Distinguish pre-match data from post-match data; enforce no look-ahead leakage. Archive immutable prediction versions with timestamps, evidence IDs, model version, and later actual result.
- Independent models for 1X2, draw, score distribution, official integer handicap, Asian handicap, totals, half/full time; calibrated probabilities and no-bet when data insufficient. Never infer draw merely from balanced odds.
- Track sources as candidates until access terms and fields are verified; no unauthorized scraping or access-control circumvention.
- New source discoveries and material changes require an append-only log: date, link, data fields, access/terms, evidence, validation result, decision, next action.
- Compare source values using event identity, kickoff UTC, team aliases, and league; flag conflicts rather than averaging.

## Source register
| Source | Purpose | Current status | Caveat |
|---|---|---|---|
| ESPN public scoreboard/summary/standings | fixtures, results, basic team statistics | VERIFIED HTTP requests in GitHub Actions 2026-10-12 | field-level completeness still needs audit; not JC fixture list |
| Chinese Sports Lottery (sporttery.cn) | official JC events, integer handicap, SP | CANDIDATE | no verified machine-readable feed |
| football-data.org | second fixture/result/standings feed | CANDIDATE | free API key required, rate/coverage limits |
| OpenFootball | historical scores and regression tests | CANDIDATE | community data; not live |
| Understat | xG/xGA | CANDIDATE | limited leagues, no confirmed licensed public API |
| Sofascore | match statistics, lineups | MANUAL_REFERENCE | official FAQ says it does not supply data API endpoints |
| FotMob | match statistics, xG and lineup reference | MANUAL_REFERENCE | access and reuse permissions unverified |
| Nowgoal | bookmaker odds and Asian handicap reference | MANUAL_REFERENCE | historical automated feed and permission unverified |
| OddsPortal | bookmaker odds comparison | MANUAL_REFERENCE | automated access and terms unverified |
| Transfermarkt | injuries and player reference | MANUAL_REFERENCE | no authorized automation established |
| FBref | historical basic football stats | LIMITED | advanced provider data removed January 2026 |
| StatsBomb Open Data | historical event data for research | CANDIDATE | sample competitions; not comprehensive current match feed |

## Evidence/decision log
- 2026-10-12: ESPN collector succeeded: 18 events across 12 league requests; enrichment 27/27 HTTP requests succeeded. Field coverage and correct JC mapping NOT YET VERIFIED. GitHub run: https://github.com/MissC1205/automation-scripts/actions/runs/38196405854
- 2026-10-12: Sofascore official FAQ explicitly states no sports-data API endpoints offered: https://sofascore.helpscoutdocs.com/article/129-sports-data-api-availability
- 2026-10-12: FBref provider announced advanced-data deletion Jan 20, 2026: https://www.sports-reference.com/blog/category/statgeekery/
- 2026-10-12: soccerdata offers multi-source adapters but warns about scraping rights and site changes: https://github.com/probberechts/soccerdata

## Required daily output
For every match: identity check, data coverage by field, source timestamps, last 5/10 completed games, home/away splits, xG if validated, injuries/lineups if verified, official SP/handicap if available, odds movement if sourced, market-specific probabilities and confidence, reasons and counterevidence, PASS if insufficient, and next-day outcome/CLV/calibration review.

This registry documents rules and discoveries. It does not claim the candidate feeds are connected or the probability models implemented.
