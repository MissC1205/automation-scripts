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

## 2026-10-14 live probes (verified by GitHub Actions)

- Official fixed-odds calculator: the prior MFM probe omitted required `channel=c` and `poolCode=had,hhad,crs,ttg,hafu`. Request and market-row validation were corrected and four offline tests passed. GitHub run https://github.com/MissC1205/automation-scripts/actions/runs/38540103655 succeeded as a workflow, but its persisted real HTTP response was **567**, and **zero verified official SP rows** were collected. Do NOT describe this as official odds coverage.
- Caidao (采道) public H5, `http://zk.bjjckx.com/`: GitHub runner DNS resolves to 121.89.172.252, HTTP landing and two JavaScript bundles returned 200; HTTPS connection was refused. Evidence: `mfm-data/source-diagnostics/20261014T171120+0800_caidao.json`.
- Read-only API methods extracted directly from the served public H5 JS: `POST /api/web/game/getLeagueMatchList`, `getWorldCupOddsList`, `getSpfzstdetail`, `getRqSpfzstdetail`, and `getJcZstDetail`. The first two returned HTTP 200/business status 200 to empty-parameter probes; the remaining three returned HTTP 200/business status 400. Evidence: `mfm-data/source-diagnostics/20261014T171808+0800_caidao_api.json`. **No match-level data, SP history, or odds rows have yet been proven accessible.** No login, CAPTCHA, token, or access control was bypassed.
- Source decision: Caidao is a verified **public H5/API reachability candidate**, not a validated odds provider or licensed data feed. Next validation requires an authorized, read-only match-ID parameter contract, rows for 008/011 cross-checked against time-stamped screenshots, and usage-rights review.


## 2026-10-14 public Caidao fixture/detail collection (source-observed, not official-verified)

- **Confirmed public H5 request**: `GET http://zk.bjjckx.com/api/web/game/footballQuery?type=0`. The actual page uses `getScoresLive({data:{type:current,userId:...}})`. Without authentication, `type=0` returned 13 upcoming rows, JC display numbers 002–014, including `matchInfo`, team names, kickoff, `spfOdds`, `rqspfOdds`, `concedeNum`, totals, score and half/full-time prices. `type=1` returned 340 historical result rows, one belonging to today's JC001. Identity, times and price values originate from Caidao and still require official-provider cross-check.
- **Match details**: `POST /api/web/game/getMatchAllData` with form field `matchInfo=FYYYYMMDDNNN` returned valid `data` dictionaries for 008 and 011, then all 14 unique fixture IDs, source-stamped 2026-10-14 17:56 Asia/Shanghai. Key JSON strings parse as `historyDataStr`, `matchFeatureStr`, `injurySuspensionStr`, `okMatchDataStr`, `poissonDistributionStr`, `matchTableStr`, `ttylIndexStr`. This is **schema coverage**, not complete or independently verified per-field data. Evidence: `mfm-data/caidao-coverage/2026-10-14-175614.json`.
- **Prematch warning**: 13 details collected before kickoff, 001 already started/finished and must not enter a historical prematch backtest. `historyDataStr.matchList` is empty for 003,005,010; a nonempty history schema does not imply actual head-to-head coverage. Likewise injury `home`/`away` objects have keys but must NOT be interpreted as confirmed injury counts.
- **Market examples**: Caidao public snapshot at 17:56 gave 008 `3.40/3.88/1.73` (home/draw/away) with handicap `+1`, and 011 `1.83/3.80/3.13` with handicap `-1`. Those are third-party reported SP values, NOT freshly authenticated official SP.
- **SP history remains unavailable**: Public read-only probes of `getSpfzstdetail`, `getRqSpfzstdetail`, `getJcOddsDetail` using public fixture IDs and related match IDs did not retrieve a history row (business 400, HTTP 500, or null payload). Evidence: `mfm-data/source-diagnostics/20261014T180014+0800_caidao_sp_history.json`. Do not claim intra-day tick history.
- **Source status**: Caidao public H5/API availability and today's fixture/field coverage VERIFIED as source observations. Data validity, historical SP completeness, provider licensing/reuse rights, independent official comparison and comprehensive predictive feature availability **UNVERIFIED**. Provider's own poisson/prognoses must never be inputs to MFM independent prediction.


## 2026-10-14 18:16 Beijing — Caidao SPF series verified

- Public fixture endpoint: `GET /api/web/game/footballQuery?type=0` found 13 unstarted/in-play list items; `type=1` included JC 001 in recent results. Join key `matchInfo=F202610140NNN`, with internal source match names and timestamps.
- Public match detail: `POST /api/web/game/getMatchAllData`, `matchInfo`, provided nonempty structured features for all 14 sales-day events as of approximately 18:02 (10 were still pre-kickoff; 4 were at/after kickoff). Coverage audit: `mfm-data/caidao-coverage/2026-10-14-180205.json`. Existence of `injurySuspensionStr` does NOT prove injury authenticity or record completeness; provider probability outputs must not be weighted into MFM.
- **Historical SPF**: `POST /api/web/game/getJcOddsDetail`, `matchInfo`. Read `result.oddsDetails[]`, NOT `data`. Each public row: `updateTime`, `odds` (home|draw|away), `oddsflag`, `num`. 18:15–18:16 source-stamped collector obtained **79 valid rows across 14/14 matches**, internal fixture names and ID pairs consistent. Evidence: `mfm-data/caidao-history/2026-10-14/20261014T181612+0800.json`. Independent of direct official SP; all quotes third-party reported.
- Screenshot verification: 008 2026-10-14 13:26:59 = `3.35|3.85|1.75`; 011 six 2026-10-13..14 SP quotations match supplied screenshot, plus later value 2026-10-14 17:49:22 = `1.83|3.80|3.13`. Evidence: `mfm-data/source-diagnostics/20261014T181321+0800_caidao_odds_structure.json`.
- `wf=rqspf` POST to `getJcOddsDetail` still returns `wf=spf`; **no true handicap SP time-series validated**. Evidence: `mfm-data/source-diagnostics/20261014T181801+0800_caidao_handicap_probe.json`. Current handicap `rqspfOdds` and `concedeNum` do exist in fixture feed, but should not be called historical handicap odds.
- Look-ahead policy: snapshots retrieved after kickoff for 001–004 cannot be marked as having been collected before kickoff even if rows claim older `updateTime` values. Store both independent retrieval time and source-reported historical event time. These are not immutable pre-match model outputs.
- 2026-10-14 MFM API-Football quota fix: core workflow push paths narrowed to core collector scripts; Caidao exploratory edits should not retrigger full football API collection.
- Status: Caidao historical SPF public-read access verified; terms/licensing and field-level accuracy not established; official bookmaker feed remains HTTP 567 in GitHub. No independent calibrated match-probability engine or EV proof.
